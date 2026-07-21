import socket
import threading
import datetime
import os
import csv
import json
import hashlib
import time
import signal
import re

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

USERS_FILE = "users.json"
CHAT_LOG = "chat_history.csv"
SERVER_LOG = "server_log.txt"
SECURITY_LOG = "security_log.txt"
PERF_LOG = "performance_results.csv"

DEFAULT_SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "listen_backlog": 20,
    "recv_buffer_size": 4096,
    "heartbeat_timeout_seconds": 30,
    "reaper_interval_seconds": 5,
    "max_failed_attempts": 5,
    "lockout_duration_seconds": 60,
    "max_message_length": 500,
    "max_concurrent_clients": 15,
    "perf_sample_interval_seconds": 5
}

def load_config(path="config.json"):
    cfg = DEFAULT_SERVER_CONFIG.copy()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                user_cfg = json.load(f).get("server", {})
            cfg.update(user_cfg)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[CONFIG] Failed to load {path}, using defaults: {e}")
    return cfg

CONFIG = load_config()

connection_semaphore = threading.Semaphore(CONFIG["max_concurrent_clients"])

login_attempts = {}
login_lock = threading.Lock()

def validate_username(username):
    return bool(re.fullmatch(r"[A-Za-z0-9_]{3,20}", username))

def is_locked_out(username):
    with login_lock:
        info = login_attempts.get(username)
        if info and info["locked_until"] > time.time():
            return True, info["locked_until"] - time.time()
        return False, 0

def record_failed_login(username):
    with login_lock:
        info = login_attempts.setdefault(username, {"count": 0, "locked_until": 0})
        info["count"] += 1
        if info["count"] >= CONFIG["max_failed_attempts"]:
            info["locked_until"] = time.time() + CONFIG["lockout_duration_seconds"]
            info["count"] = 0

def record_successful_login(username):
    with login_lock:
        login_attempts.pop(username, None)

HOST = CONFIG["host"]
PORT = CONFIG["port"]

clients = {}
logged_in_users = set()
clients_lock = threading.Lock()
shutdown_event = threading.Event()

stats = {"messages": 0, "broadcasts": 0, "private": 0}

if not os.path.exists(CHAT_LOG):
    with open(CHAT_LOG, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "sender", "receiver", "message_type", "message"])

if not os.path.exists(SERVER_LOG):
    open(SERVER_LOG, "w").close()

if not os.path.exists(SECURITY_LOG):
    open(SECURITY_LOG, "w").close()

if not os.path.exists(PERF_LOG):
    with open(PERF_LOG, "w", newline="") as f:
        csv.writer(f).writerow(
            ["timestamp", "active_connections", "messages_per_sec", 
             "avg_latency_ms", "cpu_percent", "memory_mb"]
        )

perf_lock = threading.Lock()
latency_samples = []

if PSUTIL_AVAILABLE:
    _perf_process = psutil.Process(os.getpid())
    _perf_process.cpu_percent(interval=None)  


def load_users():
    if not os.path.exists(USERS_FILE):
        raise FileNotFoundError(f"{USERS_FILE} not found. Create it before starting the server.")
    with open(USERS_FILE, "r") as f:
        return json.load(f)

USERS = load_users()

def timestamp():
    return datetime.datetime.now().strftime("%H:%M:%S")

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_credentials(username, password):
    if username not in USERS:
        return False
    return USERS[username] == hash_password(password)

def log_server_event(event, username, ip):
    line = f"{timestamp()},{event},{username},{ip}\n"
    with open(SERVER_LOG, "a") as f:
        f.write(line)
    print(f"[LOG] {line.strip()}")

def log_security(event, username, ip, detail=""):
    line = f"{timestamp()},{event},{username},{ip},{detail}\n"
    with open(SECURITY_LOG, "a") as f:
        f.write(line)
    print(f"[SECURITY] {line.strip()}")

def log_chat(sender, receiver, msg_type, message):
    with open(CHAT_LOG, "a", newline="") as f:
        csv.writer(f).writerow([timestamp(), sender, receiver, msg_type, message])

def get_last_messages(username, n=5):
    if not os.path.exists(CHAT_LOG):
        return []
    with open(CHAT_LOG, "r", newline="") as f:
        rows = list(csv.reader(f))[1:]
    sent_by_user = [r for r in rows if len(r) == 5 and r[1] == username]
    return sent_by_user[-n:]

def find_socket_by_username(username):
    with clients_lock:
        for sock, info in clients.items():
            if info["username"] == username:
                return sock
    return None

def broadcast(message):
    encoded = message.encode("utf-8")
    with clients_lock:
        targets = list(clients.keys())
    for sock in targets:
        try:
            sock.sendall(encoded)
        except Exception:
            pass

def read_login_line(conn):
    """Reads bytes until a newline is found. Returns (line_bytes, remainder_bytes).
    line_bytes is None if the connection closed before a full line arrived."""
    buffer = b""
    while b"\n" not in buffer:
        chunk = conn.recv(1024)
        if not chunk:
            return None, buffer
        buffer += chunk
    line, _, rest = buffer.partition(b"\n")
    return line, rest

def process_message(conn, username, message):
    if not message:
        return

    if message == "/heartbeat":
        return

    if len(message) > CONFIG["max_message_length"]:
        conn.sendall(b"[SERVER] Message rejected: exceeds maximum length.\n")
        log_security("INVALID_INPUT", username, "-", f"oversized message ({len(message)} chars)")
        return

    if message.startswith("/") and message != "/list" and not message.startswith("/msg "):
        conn.sendall(f"[SERVER] Unsupported command: {message.split()[0]}\n".encode())
        log_security("INVALID_INPUT", username, "-", f"unsupported command: {message}")
        return

    stats["messages"] += 1

    if message == "/list":
        with clients_lock:
            names = [info["username"] for info in clients.values()]
        conn.sendall(f"[SERVER] Online: {', '.join(names)}\n".encode())
        return

    if message.startswith("/msg "):
        parts = message.split(" ", 2)
        if len(parts) < 3:
            conn.sendall(b"[SERVER] Usage: /msg <username> <message>\n")
        else:
            target_user, priv_msg = parts[1], parts[2]
            target_sock = find_socket_by_username(target_user)
            if target_sock:
                target_sock.sendall(f"[PM from {username}] {priv_msg}\n".encode())
                conn.sendall(f"[PM to {target_user}] {priv_msg}\n".encode())
                log_chat(username, target_user, "private", priv_msg)
                stats["private"] += 1
            else:
                conn.sendall(f"[SERVER] User '{target_user}' not found.\n".encode())
        return

    log_chat(username, "ALL", "broadcast", message)
    stats["broadcasts"] += 1
    broadcast(f"[{username}] {message}\n")

def close_client_connection(conn):
    """Shared cleanup for both the reaper thread and graceful shutdown.
    Closing the socket unblocks the owning handle_client() thread's recv(),
    which then runs its existing finally block (logging, dict cleanup, broadcast)."""
    try:
        conn.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        conn.close()
    except OSError:
        pass

def reap_stale_clients():
    """Background thread: closes sockets that haven't sent anything
    (including heartbeats) within heartbeat_timeout_seconds."""
    timeout = CONFIG["heartbeat_timeout_seconds"]
    interval = CONFIG["reaper_interval_seconds"]
    while not shutdown_event.wait(interval):
        now = time.time()
        stale = []
        with clients_lock:
            for conn, info in clients.items():
                if now - info.get("last_seen", now) > timeout:
                    stale.append((conn, info["username"]))
        for conn, uname in stale:
            print(f"[REAPER] {uname} timed out, closing connection")
            close_client_connection(conn)

def record_latency(sample_ms):
    with perf_lock:
        latency_samples.append(sample_ms)

def get_cpu_percent():
    if PSUTIL_AVAILABLE:
        return _perf_process.cpu_percent(interval=None)
    try:
        return os.getloadavg()[0] * 100 / os.cpu_count()
    except (OSError, AttributeError):
        return 0.0

def get_memory_mb():
    if PSUTIL_AVAILABLE:
        return _perf_process.memory_info().rss / (1024 * 1024)
    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except OSError:
        pass
    return 0.0

def performance_monitor():
    interval = CONFIG.get("perf_sample_interval_seconds", 5)
    last_msg_count = 0
    while not shutdown_event.wait(interval):
        with clients_lock:
            active = len(clients)
        current_msg_count = stats["messages"]
        msgs_per_sec = (current_msg_count - last_msg_count) / interval
        last_msg_count = current_msg_count
        
        with perf_lock:
            samples = latency_samples[:]
            latency_samples.clear()
            
        avg_latency = sum(samples) / len(samples) if samples else 0.0
        
        with open(PERF_LOG, "a", newline="") as f:
            csv.writer(f).writerow([
                timestamp(), active, round(msgs_per_sec, 2),
                round(avg_latency, 2), round(get_cpu_percent(), 2),
                round(get_memory_mb(), 2)
            ])

def handle_client(conn, addr):
    ip = addr[0]
    port = addr[1]
    username = None

    if not connection_semaphore.acquire(blocking=False):
        try:
            conn.sendall((json.dumps({"status": "error", "reason": "server_busy"}) + "\n").encode())
        except OSError:
            pass
        conn.close()
        print(f"[SERVER] Rejected {addr} - max concurrent clients reached")
        return

    try:
        line, remainder = read_login_line(conn)
        if line is None:
            conn.close()
            return

        try:
            req = json.loads(line.decode("utf-8"))
        except json.JSONDecodeError:
            conn.sendall((json.dumps({"status": "error", "reason": "bad_request"}) + "\n").encode())
            conn.close()
            return

        if req.get("action") != "login":
            conn.sendall((json.dumps({"status": "error", "reason": "bad_request"}) + "\n").encode())
            conn.close()
            return

        username = req.get("username", "").strip()
        password = req.get("password", "")

        if not username or not password:
            conn.sendall((json.dumps({"status": "error", "reason": "missing_fields"}) + "\n").encode())
            conn.close()
            return

        if not validate_username(username):
            log_security("LOGIN_REJECTED", username, ip, "invalid username format")
            conn.sendall((json.dumps({"status": "error", "reason": "invalid_username"}) + "\n").encode())
            conn.close()
            return

        locked, remaining = is_locked_out(username)
        if locked:
            log_security("LOGIN_BLOCKED", username, ip, f"locked out for {int(remaining)}s")
            conn.sendall((json.dumps({"status": "error", "reason": "account_locked"}) + "\n").encode())
            conn.close()
            return

        if not verify_credentials(username, password):
            record_failed_login(username)
            log_security("LOGIN_FAILED", username, ip, "invalid credentials")
            conn.sendall((json.dumps({"status": "error", "reason": "invalid_credentials"}) + "\n").encode())
            conn.close()
            return

        record_successful_login(username)

        with clients_lock:
            if username in logged_in_users:
                already_logged_in = True
            else:
                already_logged_in = False
                logged_in_users.add(username)

        if already_logged_in:
            log_security("DUPLICATE_LOGIN", username, ip, "rejected - already online")
            conn.sendall((json.dumps({"status": "error", "reason": "duplicate_login"}) + "\n").encode())
            conn.close()
            return

        conn.sendall((json.dumps({"status": "success", "message": "Login successful"}) + "\n").encode())
        log_security("LOGIN_SUCCESS", username, ip, "authenticated")

        with clients_lock:
            clients[conn] = {
                "username": username,
                "ip": ip,
                "port": port,
                "login_time": timestamp(),
                "last_seen": time.time(),
            }

        log_server_event("CONNECTED", username, ip)
        broadcast(f"[SERVER] {username} has joined the chat!\n")

        history = get_last_messages(username, 5)
        if history:
            conn.sendall(b"[SERVER] Your last messages:\n")
            for row in history:
                ts, sender, receiver, mtype, msg = row
                conn.sendall(f"  ({ts}) [{mtype} -> {receiver}] {msg}\n".encode())

        if remainder:
            leftover_text = remainder.decode("utf-8", errors="ignore").strip()
            if leftover_text:
                with clients_lock:
                    if conn in clients:
                        clients[conn]["last_seen"] = time.time()
                t0 = time.perf_counter()
                process_message(conn, username, leftover_text)
                record_latency((time.perf_counter() - t0) * 1000)

        while True:
            data = conn.recv(CONFIG["recv_buffer_size"])
            if not data:
                break
            message = data.decode("utf-8").strip()
            if not message:
                continue
            with clients_lock:
                if conn in clients:
                    clients[conn]["last_seen"] = time.time()
            t0 = time.perf_counter()
            process_message(conn, username, message)
            record_latency((time.perf_counter() - t0) * 1000)

    except Exception as e:
        print(f"[ERROR] {username or addr}: {e}")
    finally:
        with clients_lock:
            if conn in clients:
                del clients[conn]
            if username and username in logged_in_users:
                logged_in_users.discard(username)
        conn.close()
        if username:
            log_server_event("DISCONNECTED", username, ip)
            log_security("LOGOUT", username, ip, "disconnected")
            broadcast(f"[SERVER] {username} has left the chat.\n")
        connection_semaphore.release()

def graceful_shutdown(server_sock):
    """Notifies connected clients, closes their sockets, and releases
    the listening socket before the process exits."""
    print("[SERVER] Notifying connected clients of shutdown...")
    broadcast("[SERVER] Server is shutting down. You will be disconnected.\n")
    with clients_lock:
        conns = list(clients.keys())
    for conn in conns:
        close_client_connection(conn)
    time.sleep(0.5)
    try:
        server_sock.close()
    except OSError:
        pass
    with clients_lock:
        online = len(clients)
    print(f"[STATS] Online={online} Msgs={stats['messages']} "
          f"Broadcasts={stats['broadcasts']} Private={stats['private']}")
    print("[SERVER] Shutdown complete.")

def _signal_handler(signum, frame):
    print(f"\n[SERVER] Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()

def main():
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(CONFIG["listen_backlog"])
    server.settimeout(1.0)
    
    print(f"[SERVER] Listening on {HOST}:{PORT}")
    
    threading.Thread(target=reap_stale_clients, daemon=True).start()
    threading.Thread(target=performance_monitor, daemon=True).start()
    
    while not shutdown_event.is_set():
        try:
            conn, addr = server.accept()
        except socket.timeout:
            continue
        except OSError:
            break
            
        print(f"[SERVER] New connection from {addr}")
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()
        
    graceful_shutdown(server)

if __name__ == "__main__":
    main()