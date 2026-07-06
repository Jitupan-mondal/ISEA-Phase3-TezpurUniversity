import socket
import threading

SERVER_IP = "10.0.0.1"
SERVER_PORT = 5000


def receive_messages(sock):
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                print("\n[CLIENT] Disconnected from server.")
                break
            print(data.decode("utf-8"), end="", flush=True)
        except Exception:
            break


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    username = input("Enter Username: ").strip()
    sock.sendall(username.encode("utf-8"))

    t = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    t.start()

    print("[CLIENT] Commands: /msg <user> <message>, /list, /quit")
    try:
        while True:
            msg = input()
            if msg.strip() == "":
                continue
            if msg.strip().lower() == "/quit":
                break
            sock.sendall(msg.encode("utf-8"))
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        sock.close()


if __name__ == "__main__":
    main()