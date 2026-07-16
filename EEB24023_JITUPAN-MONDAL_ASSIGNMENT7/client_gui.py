import socket
import threading
import queue
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox

# ==========================================
# 1. Network Logic (Independent of GUI)
# ==========================================
class NetworkClient:
    def __init__(self, host='10.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.msg_queue = queue.Queue()
        self._buffer = b""

    def _read_line(self):
        while b"\n" not in self._buffer:
            chunk = self.sock.recv(1024)
            if not chunk:
                return None
            self._buffer += chunk
        line, _, rest = self._buffer.partition(b"\n")
        self._buffer = rest
        return line

    def connect(self, username, password):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))

            login_request = json.dumps({
                "action": "login",
                "username": username,
                "password": password
            }) + "\n"
            self.sock.sendall(login_request.encode('utf-8'))

            line = self._read_line()
            if line is None:
                self.sock.close()
                return False, "no_response"

            response = json.loads(line.decode('utf-8'))

            if response.get("status") == "success":
                self.running = True
                threading.Thread(target=self.receive_loop, daemon=True).start()
                return True, "ok"
            else:
                self.sock.close()
                return False, response.get("reason", "unknown_error")

        except Exception as e:
            print(f"Connection error: {e}")
            return False, "connection_error"

    def receive_loop(self):
        if self._buffer:
            leftover = self._buffer.decode('utf-8', errors='ignore')
            self._buffer = b""
            if leftover:
                self.msg_queue.put(leftover)

        while self.running:
            try:
                data = self.sock.recv(1024).decode('utf-8')
                if data:
                    self.msg_queue.put(data)
                else:
                    self.running = False
                    self.msg_queue.put("[SYSTEM] Disconnected from server.")
                    break
            except Exception:
                self.running = False
                break

    def send(self, message):
        if self.sock and self.running:
            try:
                self.sock.send(message.encode('utf-8'))
            except Exception as e:
                print(f"Send error: {e}")

    def disconnect(self):
        self.running = False
        if self.sock:
            self.sock.close()


# ==========================================
# 2. Login Window (GUI)
# ==========================================
class LoginWindow:
    def __init__(self, root, on_success_callback):
        self.root = root
        self.on_success_callback = on_success_callback
        self.root.title("Chat Login")
        self.root.geometry("320x200")

        tk.Label(root, text="Username:").pack(pady=(15, 0))
        self.username_entry = tk.Entry(root)
        self.username_entry.pack(pady=5)

        tk.Label(root, text="Password:").pack(pady=(5, 0))
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.pack(pady=5)

        self.connect_btn = tk.Button(root, text="Connect", command=self.attempt_login)
        self.connect_btn.pack(pady=15)

        self.password_entry.bind("<Return>", lambda event: self.attempt_login())

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
            return
        if not password:
            messagebox.showerror("Error", "Password cannot be empty.")
            return

        self.connect_btn.config(state="disabled")
        self.root.after(50, lambda: self._do_login(username, password))

    def _do_login(self, username, password):
        self.on_success_callback(username, password)
        self.connect_btn.config(state="normal")


# ==========================================
# 3. Main Chat Window (GUI)
# ==========================================
class ChatWindow:
    def __init__(self, root, network_client, username):
        self.root = root
        self.network = network_client
        self.username = username
        self.root.title(f"Chat Room - {self.username}")
        self.root.geometry("600x400")

        chat_frame = tk.Frame(self.root)
        chat_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, state='disabled', height=15)
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        user_frame = tk.Frame(self.root)
        user_frame.pack(padx=10, pady=5, fill=tk.X)
        tk.Label(user_frame, text="Online Users:").pack(side=tk.LEFT)

        self.user_listbox = tk.Listbox(user_frame, height=3)
        self.user_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        input_frame = tk.Frame(self.root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        self.msg_entry = tk.Entry(input_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.msg_entry.bind("<Return>", lambda event: self.send_message())

        self.send_btn = tk.Button(input_frame, text="Send", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        self.disconnect_btn = tk.Button(input_frame, text="Disconnect", command=self.disconnect)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        self.poll_queue()
        self.network.send("/list")

    def poll_queue(self):
        while not self.network.msg_queue.empty():
            msg = self.network.msg_queue.get()
            self.display_message(msg)
            if "Online:" in msg:
                self.update_user_list(msg)
            elif "has joined the chat" in msg or "has left the chat" in msg:
                self.network.send("/list")
        self.root.after(100, self.poll_queue)

    def display_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.yview(tk.END)
        self.chat_display.config(state='disabled')

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if msg:
            self.network.send(msg)
            self.msg_entry.delete(0, tk.END)

    def update_user_list(self, msg):
        self.user_listbox.delete(0, tk.END)
        try:
            users_str = msg.split(":", 1)[1].strip()
            users = users_str.split(",")
            for u in users:
                self.user_listbox.insert(tk.END, u.strip())
        except Exception:
            pass

    def disconnect(self):
        self.network.disconnect()
        self.root.destroy()


# ==========================================
# 4. Application Main Flow
# ==========================================
LOGIN_ERROR_MESSAGES = {
    "invalid_credentials": "Incorrect username or password.",
    "duplicate_login": "This user is already logged in from another location.",
    "missing_fields": "Username and password cannot be empty.",
    "bad_request": "Login failed due to a protocol error.",
    "connection_error": "Could not connect to the server.",
    "no_response": "No response received from the server.",
}


def main():
    root = tk.Tk()
    network = NetworkClient()  # Default expects server at 10.0.0.1 (h1 in Mininet)

    def on_login_success(username, password):
        success, reason = network.connect(username, password)
        if success:
            for widget in root.winfo_children():
                widget.destroy()
            ChatWindow(root, network, username)
        else:
            error_text = LOGIN_ERROR_MESSAGES.get(reason, reason)
            messagebox.showerror("Login Failed", error_text)

    LoginWindow(root, on_login_success)

    root.protocol("WM_DELETE_WINDOW", lambda: (network.disconnect(), root.destroy()))

    root.mainloop()


if __name__ == "__main__":
    main()
