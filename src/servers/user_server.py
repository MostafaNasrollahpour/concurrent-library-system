import socket
import threading
from ..persistence import load_json, save_json
from ..config import USERS_FILE
from ..logger import log_message


class UserServer:
    def __init__(self, port):
        self.port = port
        data = load_json(USERS_FILE, {"users": {}, "next_id": 1, "user_ids": []})
        self.users = data["users"]
        self.user_ids = set(data["user_ids"])
        self.next_id = data["next_id"]
        self.lock = threading.Lock()
    
    def handle_connection(self, conn):
        """Handle a single client connection"""
        try:
            data = conn.recv(1024).decode().strip()
            parts = data.split()
            if not parts:
                return
            
            cmd = parts[0]
            if cmd == "register":
                self.handle_register(conn, parts)
            elif cmd == "check":
                self.handle_check(conn, parts)
        except Exception as e:
            log_message(f"User server connection error: {e}")
        finally:
            conn.close()
    
    def handle_register(self, conn, parts):
        """Handle user registration"""
        name = ' '.join(parts[1:])
        with self.lock:
            if name in self.users:
                conn.send("failure".encode())
                log_message(f"Failed register user {name}: exists")
            else:
                user_id = str(self.next_id)
                self.next_id += 1
                self.users[name] = user_id
                self.user_ids.add(user_id)
                save_json(USERS_FILE, {
                    "users": self.users,
                    "next_id": self.next_id,
                    "user_ids": list(self.user_ids)
                })
                conn.send(f"success {user_id}".encode())
                log_message(f"Registered user {name} ID {user_id}")
    
    def handle_check(self, conn, parts):
        """Handle user ID validation"""
        if len(parts) < 2:
            conn.send("failure".encode())
            return
        
        user_id = parts[1]
        with self.lock:
            resp = "success" if user_id in self.user_ids else "failure"
            conn.send(resp.encode())
            log_message(f"Checked user {user_id}: {resp}")
    
    def run(self):
        """Start the user server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', self.port))
        sock.listen(10)
        log_message(f"User server started on port {self.port}")
        
        while True:
            conn, addr = sock.accept()
            threading.Thread(target=self.handle_connection, args=(conn,)).start()


def run_user_server(port):
    """Function to run user server"""
    server = UserServer(port)
    server.run()