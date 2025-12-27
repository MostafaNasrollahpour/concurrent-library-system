"""Main library server that coordinates between user and book servers"""
import os
import socket
from ..config import USER_PORT, BOOK_PORT
from ..logger import log_message


class MainServer:
    def __init__(self, port, user_port, book_port):
        self.port = port
        self.user_port = user_port
        self.book_port = book_port
    
    def send_to_server(self, server_port, message):
        """Send a message to a server and get response"""
        try:
            with socket.socket() as sock:
                sock.connect(('localhost', server_port))
                sock.send(message.encode())
                return sock.recv(1024).decode()
        except Exception as e:
            log_message(f"Error connecting to server on port {server_port}: {e}")
            return "failure"
    
    def handle_command(self, conn, data):
        """Handle a single command from client"""
        parts = data.split()
        if not parts:
            return "failure"
        
        cmd = parts[0]
        response = "failure"
        
        try:
            if cmd == "register_user":
                name = ' '.join(parts[1:])
                response = self.send_to_server(self.user_port, f"register {name}")
            
            elif cmd == "register_book":
                title = ' '.join(parts[1:])
                response = self.send_to_server(self.book_port, f"register {title}")
            
            elif cmd == "lend_book":
                if len(parts) < 3:
                    return "failure"
                user_id = parts[1]
                title = ' '.join(parts[2:])
                # Check user exists first
                check_resp = self.send_to_server(self.user_port, f"check {user_id}")
                if check_resp == "success":
                    response = self.send_to_server(self.book_port, f"lend {user_id} {title}")
            
            elif cmd == "return_book":
                if len(parts) < 3:
                    return "failure"
                user_id = parts[1]
                title = ' '.join(parts[2:])
                # Check user exists first
                check_resp = self.send_to_server(self.user_port, f"check {user_id}")
                if check_resp == "success":
                    response = self.send_to_server(self.book_port, f"return {user_id} {title}")
        
        except Exception as e:
            log_message(f"Error handling command {cmd}: {e}")
            response = "failure"
        
        return response
    
    def handle_client(self, conn):
        """Handle a single client connection in forked process"""
        try:
            data = conn.recv(1024).decode().strip()
            response = self.handle_command(conn, data)
            conn.send(response.encode())
            log_message(f"Handled {data}: {response}")
        except Exception as e:
            log_message(f"Main server client error: {e}")
            conn.send("failure".encode())
        finally:
            conn.close()
            os._exit(0)
    
    def run(self):
        """Start the main server with forking"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', self.port))
        sock.listen(10)
        log_message(f"Main library server started on port {self.port}")
        
        while True:
            try:
                client_conn, addr = sock.accept()
                pid = os.fork()
                if pid == 0:
                    sock.close()
                    self.handle_client(client_conn)
                else:
                    client_conn.close()
            except Exception as e:
                log_message(f"Main server accept error: {e}")


def run_main_server(port, user_port, book_port):
    """Function to run main server"""
    server = MainServer(port, user_port, book_port)
    server.run()