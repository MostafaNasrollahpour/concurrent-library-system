"""Main entry point for the library system"""
import os
import sys
from src.servers.user_server import run_user_server
from src.servers.book_server import run_book_server
from src.servers.main_server import run_main_server
from src.processes.user_process import run_user_process
from src.config import MAIN_PORT, USER_PORT, BOOK_PORT, LOG_FILE
from src.logger import log_message


def cleanup_log():
    """Clear log file at startup"""
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    open(LOG_FILE, "w").close()


def start_library_system():
    """Start all library servers in child processes"""
    # Start user server
    user_pid = os.fork()
    if user_pid == 0:
        run_user_server(USER_PORT)
        os._exit(0)
    
    # Start book server
    book_pid = os.fork()
    if book_pid == 0:
        run_book_server(BOOK_PORT)
        os._exit(0)
    
    # Start main server
    run_main_server(MAIN_PORT, USER_PORT, BOOK_PORT)
    
    # Wait for child processes (though main server runs forever)
    os.waitpid(user_pid, 0)
    os.waitpid(book_pid, 0)


def start_user_processes(user_files):
    """Start user processes for each command file"""
    user_pids = []
    
    for cmd_file in user_files:
        user_name = os.path.basename(cmd_file).split('.')[0]
        user_pid = os.fork()
        
        if user_pid == 0:
            run_user_process(user_name, cmd_file, MAIN_PORT)
            os._exit(0)
        
        user_pids.append(user_pid)
    
    return user_pids


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python -m src.main user1.txt user2.txt ...")
        sys.exit(1)
    
    cleanup_log()
    
    # Start library system in a separate process
    library_pid = os.fork()
    if library_pid == 0:
        start_library_system()
        os._exit(0)
    
    # Start user processes
    user_files = sys.argv[1:]
    user_pids = start_user_processes(user_files)
    
    # Wait for all processes to complete
    os.waitpid(library_pid, 0)
    for pid in user_pids:
        os.waitpid(pid, 0)


if __name__ == "__main__":
    main()