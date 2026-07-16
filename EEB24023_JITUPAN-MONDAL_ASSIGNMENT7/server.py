import socket
import threading
import datetime
import os
import csv
import json
import hashlib

HOST = "0.0.0.0"
PORT = 5000

USERS_FILE = "users.json"
CHAT_LOG = "chat_history.csv"
SERVER_LOG = "server_log.txt"
SECURITY_LOG = "security_log.txt"

clients = {}
logged_in_users = set()
clients_lock = threading.Lock()

stats = {"messages": 0, "broadcasts": 0, "private": 0}

if not os.path.exists(CHAT_LOG):
    with open(CHAT_LOG, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "sender", "receiver", "message_type", "message"])

if not os.path.exists(SERVER_LOG):
    open(SERVER_LOG, "w").close()

if not os.path.exists(SECURITY_LOG):
    open(SECURITY_LOG, "w").close()


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
    """Handles one plain-text chat command/message after login is complete."""
    if not message:
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


def handle_client(conn, addr):
    ip = addr[0]
    port = addr[1]
    username = None

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

        if not verify_credentials(username, password):
            log_security("LOGIN_FAILED", username, ip, "invalid credentials")
            conn.sendall((json.dumps({"status": "error", "reason": "invalid_credentials"}) + "\n").encode())
            conn.close()
            return

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
                process_message(conn, username, leftover_text)

        while True:
            data = conn.recv(4096)
            if not data:
                break
            message = data.decode("utf-8").strip()
            if not message:
                continue
            process_message(conn, username, message)

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


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[SERVER] Listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server.accept()
            print(f"[SERVER] New connection from {addr}")
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
        with clients_lock:
            online = len(clients)
        print(f"[STATS] Online={online} Msgs={stats['messages']} Broadcasts={stats['broadcasts']} Private={stats['private']}")
    finally:
        server.close()


if __name__ == "__main__":
    main()
