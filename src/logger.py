import os
import time
import fcntl
from .config import LOG_FILE


def log_message(message):
    """Thread-safe logging with file locking"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    with open(LOG_FILE, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(f"[{timestamp}] PID:{os.getpid()} {message}\n")
        fcntl.flock(f, fcntl.LOCK_UN)