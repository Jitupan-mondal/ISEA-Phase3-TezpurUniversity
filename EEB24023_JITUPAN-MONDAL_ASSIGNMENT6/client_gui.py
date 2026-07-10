import socket
import threading
import queue
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

    def connect(self, username):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            # Send the initial username to the server
            self.sock.send(username.encode('utf-8'))
            self.running = True
            
            # Start background thread for receiving messages
            threading.Thread(target=self.receive_loop, daemon=True).start()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def receive_loop(self):
        while self.running:
            try:
                data = self.sock.recv(1024).decode('utf-8')
                if data:
                    self.msg_queue.put(data)
                else:
                    self.running = False
                    self.msg_queue.put("[SYSTEM] Disconnected from server.")
                    break
            except:
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
        self.root.geometry("300x150")

        # Layout setup
        tk.Label(root, text="Enter Username:").pack(pady=10)
        
        self.username_entry = tk.Entry(root)
        self.username_entry.pack(pady=5)
        
        self.connect_btn = tk.Button(root, text="Connect", command=self.attempt_login)
        self.connect_btn.pack(pady=10)

    def attempt_login(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
            return
        
        # Pass the valid username back to the main application flow
        self.on_success_callback(username)

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

        # Frame for Chat Area
        chat_frame = tk.Frame(self.root)
        chat_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, state='disabled', height=15)
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame for Online Users
        user_frame = tk.Frame(self.root)
        user_frame.pack(padx=10, pady=5, fill=tk.X)
        tk.Label(user_frame, text="Online Users:").pack(side=tk.LEFT)
        
        self.user_listbox = tk.Listbox(user_frame, height=3)
        self.user_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Frame for Input and Controls
        input_frame = tk.Frame(self.root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        self.msg_entry = tk.Entry(input_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.msg_entry.bind("<Return>", lambda event: self.send_message())

        self.send_btn = tk.Button(input_frame, text="Send", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        self.disconnect_btn = tk.Button(input_frame, text="Disconnect", command=self.disconnect)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        # Start polling the queue for new messages
        self.poll_queue()

        # Request initial user list from server
        self.network.send("/list")

    def poll_queue(self):
        # Check if there are messages waiting from the network thread
        while not self.network.msg_queue.empty():
            msg = self.network.msg_queue.get()
            self.display_message(msg)
            # If the server sends a list of users, update the listbox
            # Note: Adjust this parsing based on how your Assignment 5 server formats the '/list' response
            if "Online:" in msg:
                self.update_user_list(msg)
            elif "has joined the chat" in msg or "has left the chat" in msg:
                self.network.send("/list")
        # Schedule this function to run again in 100 milliseconds
        self.root.after(100, self.poll_queue)

    def display_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.yview(tk.END) # Auto-scroll to bottom
        self.chat_display.config(state='disabled')

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if msg:
            self.network.send(msg)
            self.msg_entry.delete(0, tk.END)

    def update_user_list(self, msg):
        self.user_listbox.delete(0, tk.END)
        # Extract users from a string like "Online users: Alice, Bob"
        try:
            users_str = msg.split(":")[1].strip()
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
def main():
    root = tk.Tk()
    network = NetworkClient() # Default expects server at 10.0.0.1 (h1 in Mininet)

    def on_login_success(username):
        if network.connect(username):
            # Destroy login widgets
            for widget in root.winfo_children():
                widget.destroy()
            # Initialize Chat Interface
            ChatWindow(root, network, username)
        else:
            messagebox.showerror("Connection Error", "Could not connect to the server.")

    # Start with the login window
    LoginWindow(root, on_login_success)
    
    # Handle window close event safely
    root.protocol("WM_DELETE_WINDOW", lambda: (network.disconnect(), root.destroy()))
    
    root.mainloop()

if __name__ == "__main__":
    main()