import socket
import threading
from ..persistence import load_json, save_json
from ..config import BOOKS_FILE
from ..logger import log_message


class BookServer:
    def __init__(self, port):
        self.port = port
        self.books = load_json(BOOKS_FILE, {})
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
            elif cmd == "lend":
                self.handle_lend(conn, parts)
            elif cmd == "return":
                self.handle_return(conn, parts)
        except Exception as e:
            log_message(f"Book server connection error: {e}")
        finally:
            conn.close()
    
    def handle_register(self, conn, parts):
        """Handle book registration"""
        title = ' '.join(parts[1:])
        with self.lock:
            if title in self.books:
                conn.send("failure".encode())
                log_message(f"Failed register book {title}: exists")
            else:
                self.books[title] = None
                save_json(BOOKS_FILE, self.books)
                conn.send("success".encode())
                log_message(f"Registered book {title}")
    
    def handle_lend(self, conn, parts):
        """Handle book lending"""
        if len(parts) < 3:
            conn.send("failure".encode())
            return
        
        user_id = parts[1]
        title = ' '.join(parts[2:])
        with self.lock:
            if title not in self.books or self.books[title] is not None:
                conn.send("failure".encode())
                log_message(f"Failed lend {title} to {user_id}")
            else:
                self.books[title] = user_id
                save_json(BOOKS_FILE, self.books)
                conn.send("success".encode())
                log_message(f"Lent {title} to {user_id}")
    
    def handle_return(self, conn, parts):
        """Handle book return"""
        if len(parts) < 3:
            conn.send("failure".encode())
            return
        
        user_id = parts[1]
        title = ' '.join(parts[2:])
        with self.lock:
            if title not in self.books or self.books[title] != user_id:
                conn.send("failure".encode())
                log_message(f"Failed return {title} by {user_id}")
            else:
                self.books[title] = None
                save_json(BOOKS_FILE, self.books)
                conn.send("success".encode())
                log_message(f"Returned {title} by {user_id}")
    
    def run(self):
        """Start the book server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', self.port))
        sock.listen(10)
        log_message(f"Book server started on port {self.port}")
        
        while True:
            conn, addr = sock.accept()
            threading.Thread(target=self.handle_connection, args=(conn,)).start()


def run_book_server(port):
    """Function to run book server"""
    server = BookServer(port)
    server.run()