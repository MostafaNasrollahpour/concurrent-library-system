import os
import time
import socket
from ..config import MAIN_PORT
from ..logger import log_message


class UserProcess:
    def __init__(self, user_name, cmd_file, main_port):
        self.user_name = user_name
        self.cmd_file = cmd_file
        self.main_port = main_port
        self.user_id = None
    
    def send_to_main_server(self, message):
        """Send command to main server and get response"""
        try:
            with socket.socket() as conn:
                conn.connect(('localhost', self.main_port))
                conn.send(message.encode())
                return conn.recv(1024).decode()
        except Exception as e:
            log_message(f"User {self.user_name} connection error: {e}")
            return "failure"
    
    def execute_command(self, line):
        """Execute a single command line"""
        parts = line.split()
        if not parts:
            return
        
        cmd = parts[0]
        
        try:
            if cmd == "Sleep":
                self.handle_sleep(parts)
            elif cmd == "Register":
                self.handle_register()
            elif cmd == "Register_book":
                self.handle_register_book(parts)
            elif cmd == "Lend":
                self.handle_lend(parts)
            elif cmd == "Return":
                self.handle_return(parts)
        except Exception as e:
            log_message(f"User {self.user_name} command {cmd} error: {e}")
    
    def handle_sleep(self, parts):
        """Handle Sleep command"""
        if len(parts) < 2:
            return
        seconds = float(parts[1])
        time.sleep(seconds)
        log_message(f"User {self.user_name} slept {seconds}s")
    
    def handle_register(self):
        """Handle Register command"""
        if self.user_id:
            log_message(f"User {self.user_name} already registered")
            return
        
        resp = self.send_to_main_server(f"register_user {self.user_name}")
        if resp.startswith("success "):
            self.user_id = resp.split()[1]
            log_message(f"User {self.user_name} registered ID {self.user_id}")
        else:
            log_message(f"User {self.user_name} register failed: {resp}")
    
    def handle_register_book(self, parts):
        """Handle Register_book command"""
        if len(parts) < 2:
            return
        title = ' '.join(parts[1:])
        resp = self.send_to_main_server(f"register_book {title}")
        log_message(f"User {self.user_name} register_book {title}: {resp}")
    
    def handle_lend(self, parts):
        """Handle Lend command"""
        if not self.user_id:
            log_message(f"User {self.user_name} not registered for Lend")
            return
        
        if len(parts) < 2:
            return
        title = ' '.join(parts[1:])
        resp = self.send_to_main_server(f"lend_book {self.user_id} {title}")
        log_message(f"User {self.user_name} lend {title}: {resp}")
    
    def handle_return(self, parts):
        """Handle Return command"""
        if not self.user_id:
            log_message(f"User {self.user_name} not registered for Return")
            return
        
        if len(parts) < 2:
            return
        title = ' '.join(parts[1:])
        resp = self.send_to_main_server(f"return_book {self.user_id} {title}")
        log_message(f"User {self.user_name} return {title}: {resp}")
    
    def run(self):
        """Execute all commands from the command file"""
        log_message(f"User {self.user_name} started with {self.cmd_file}")
        
        if not os.path.exists(self.cmd_file):
            log_message(f"User {self.user_name} error: {self.cmd_file} not found")
            return
        
        with open(self.cmd_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.execute_command(line)


def run_user_process(user_name, cmd_file, main_port):
    """Function to run user process"""
    process = UserProcess(user_name, cmd_file, main_port)
    process.run()