import os
import sys
import time
import socket
import threading
import fcntl
import json

LOG_FILE = "library.log"
USERS_FILE = "users.json"
BOOKS_FILE = "books.json"

# لاگ با lock
def log_message(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(LOG_FILE, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(f"[{timestamp}] PID:{os.getpid()} {message}\n")
        fcntl.flock(f, fcntl.LOCK_UN)

# بارگذاری و ذخیره persistence
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except:
            pass
    return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# سرور کاربران
def run_user_server(port):
    data = load_json(USERS_FILE, {"users": {}, "next_id": 1, "user_ids": []})
    users = data["users"]
    user_ids = set(data["user_ids"])
    next_id = data["next_id"]
    lock = threading.Lock()

    def handle(conn):
        nonlocal next_id
        try:
            data = conn.recv(1024).decode().strip()
            parts = data.split()
            cmd = parts[0]
            if cmd == "register":
                name = ' '.join(parts[1:])
                with lock:
                    if name in users:
                        conn.send("failure".encode())
                        log_message(f"Failed register user {name}: exists")
                    else:
                        user_id = str(next_id)
                        next_id += 1
                        users[name] = user_id
                        user_ids.add(user_id)
                        save_json(USERS_FILE, {"users": users, "next_id": next_id, "user_ids": list(user_ids)})
                        conn.send(f"success {user_id}".encode())
                        log_message(f"Registered user {name} ID {user_id}")
            elif cmd == "check":
                user_id = parts[1]
                with lock:
                    resp = "success" if user_id in user_ids else "failure"
                    conn.send(resp.encode())
                    log_message(f"Checked user {user_id}: {resp}")
        except Exception as e:
            log_message(f"User server error: {e}")
        finally:
            conn.close()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', port))
    sock.listen(10)
    log_message("User server started")
    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle, args=(conn,)).start()

# سرور کتاب‌ها
def run_book_server(port):
    books = load_json(BOOKS_FILE, {})
    lock = threading.Lock()

    def handle(conn):
        try:
            data = conn.recv(1024).decode().strip()
            parts = data.split()
            cmd = parts[0]
            if cmd == "register":
                title = ' '.join(parts[1:])
                with lock:
                    if title in books:
                        conn.send("failure".encode())
                        log_message(f"Failed register book {title}: exists")
                    else:
                        books[title] = None
                        save_json(BOOKS_FILE, books)
                        conn.send("success".encode())
                        log_message(f"Registered book {title}")
            elif cmd == "lend":
                user_id = parts[1]
                title = ' '.join(parts[2:])
                with lock:
                    if title not in books or books[title] is not None:
                        conn.send("failure".encode())
                        log_message(f"Failed lend {title} to {user_id}")
                    else:
                        books[title] = user_id
                        save_json(BOOKS_FILE, books)
                        conn.send("success".encode())
                        log_message(f"Lent {title} to {user_id}")
            elif cmd == "return":
                user_id = parts[1]
                title = ' '.join(parts[2:])
                with lock:
                    if title not in books or books[title] != user_id:
                        conn.send("failure".encode())
                        log_message(f"Failed return {title} by {user_id}")
                    else:
                        books[title] = None
                        save_json(BOOKS_FILE, books)
                        conn.send("success".encode())
                        log_message(f"Returned {title} by {user_id}")
        except Exception as e:
            log_message(f"Book server error: {e}")
        finally:
            conn.close()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', port))
    sock.listen(10)
    log_message("Book server started")
    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle, args=(conn,)).start()

# سرور اصلی
def run_main_server(port, user_port, book_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', port))
    sock.listen(10)
    log_message("Main library server started")
    while True:
        try:
            client_conn, addr = sock.accept()
            pid = os.fork()
            if pid == 0:
                sock.close()
                try:
                    data = client_conn.recv(1024).decode().strip()
                    parts = data.split()
                    cmd = parts[0]
                    response = "failure"
                    if cmd == "register_user":
                        name = ' '.join(parts[1:])
                        with socket.socket() as user_sock:
                            user_sock.connect(('localhost', user_port))
                            user_sock.send(f"register {name}".encode())
                            response = user_sock.recv(1024).decode()
                    elif cmd == "register_book":
                        title = ' '.join(parts[1:])
                        with socket.socket() as book_sock:
                            book_sock.connect(('localhost', book_port))
                            book_sock.send(f"register {title}".encode())
                            response = book_sock.recv(1024).decode()
                    elif cmd == "lend_book":
                        user_id = parts[1]
                        title = ' '.join(parts[2:])
                        with socket.socket() as user_sock:
                            user_sock.connect(('localhost', user_port))
                            user_sock.send(f"check {user_id}".encode())
                            check_resp = user_sock.recv(1024).decode()
                        if check_resp == "success":
                            with socket.socket() as book_sock:
                                book_sock.connect(('localhost', book_port))
                                book_sock.send(f"lend {user_id} {title}".encode())
                                response = book_sock.recv(1024).decode()
                    elif cmd == "return_book":
                        user_id = parts[1]
                        title = ' '.join(parts[2:])
                        with socket.socket() as user_sock:
                            user_sock.connect(('localhost', user_port))
                            user_sock.send(f"check {user_id}".encode())
                            check_resp = user_sock.recv(1024).decode()
                        if check_resp == "success":
                            with socket.socket() as book_sock:
                                book_sock.connect(('localhost', book_port))
                                book_sock.send(f"return {user_id} {title}".encode())
                                response = book_sock.recv(1024).decode()
                    client_conn.send(response.encode())
                    log_message(f"Handled {cmd} for {data.split()[1:]}: {response}")
                except Exception as e:
                    log_message(f"Main handle error: {e}")
                    client_conn.send("failure".encode())
                finally:
                    client_conn.close()
                    os._exit(0)
            else:
                client_conn.close()
        except Exception as e:
            log_message(f"Main server error: {e}")

# فرآیند کاربر
def run_user_process(user_name, cmd_file, main_port):
    user_id = None
    log_message(f"User {user_name} started with {cmd_file}")
    if not os.path.exists(cmd_file):
        log_message(f"User {user_name} error: {cmd_file} not found")
        return
    with open(cmd_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            cmd = parts[0]
            try:
                if cmd == "Sleep":
                    seconds = float(parts[1])
                    time.sleep(seconds)
                    log_message(f"User {user_name} slept {seconds}s")
                elif cmd == "Register":
                    if user_id:
                        log_message(f"User {user_name} already registered")
                        continue
                    with socket.socket() as conn:
                        conn.connect(('localhost', main_port))
                        conn.send(f"register_user {user_name}".encode())
                        resp = conn.recv(1024).decode()
                        if resp.startswith("success "):
                            user_id = resp.split()[1]
                            log_message(f"User {user_name} registered ID {user_id}")
                        else:
                            log_message(f"User {user_name} register failed: {resp}")
                elif cmd == "Register_book":
                    title = ' '.join(parts[1:])
                    with socket.socket() as conn:
                        conn.connect(('localhost', main_port))
                        conn.send(f"register_book {title}".encode())
                        resp = conn.recv(1024).decode()
                        log_message(f"User {user_name} register_book {title}: {resp}")
                elif cmd == "Lend":
                    if not user_id:
                        log_message(f"User {user_name} not registered for Lend")
                        continue
                    title = ' '.join(parts[1:])
                    with socket.socket() as conn:
                        conn.connect(('localhost', main_port))
                        conn.send(f"lend_book {user_id} {title}".encode())
                        resp = conn.recv(1024).decode()
                        log_message(f"User {user_name} lend {title}: {resp}")
                elif cmd == "Return":
                    if not user_id:
                        log_message(f"User {user_name} not registered for Return")
                        continue
                    title = ' '.join(parts[1:])
                    with socket.socket() as conn:
                        conn.connect(('localhost', main_port))
                        conn.send(f"return_book {user_id} {title}".encode())
                        resp = conn.recv(1024).decode()
                        log_message(f"User {user_name} return {title}: {resp}")
            except Exception as e:
                log_message(f"User {user_name} cmd {cmd} error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python library.py user1.txt user2.txt ...")
        sys.exit(1)

    open(LOG_FILE, "w").close()  # خالی کردن لاگ

    MAIN_PORT = 5000
    USER_PORT = 5001
    BOOK_PORT = 5002

    library_pid = os.fork()
    if library_pid == 0:
        user_pid = os.fork()
        if user_pid == 0:
            run_user_server(USER_PORT)
            os._exit(0)

        book_pid = os.fork()
        if book_pid == 0:
            run_book_server(BOOK_PORT)
            os._exit(0)

        run_main_server(MAIN_PORT, USER_PORT, BOOK_PORT)

        os.waitpid(user_pid, 0)
        os.waitpid(book_pid, 0)
        os._exit(0)

    user_pids = []
    for arg in sys.argv[1:]:
        user_name = os.path.basename(arg).split('.')[0]
        user_pid = os.fork()
        if user_pid == 0:
            run_user_process(user_name, arg, MAIN_PORT)
            os._exit(0)
        user_pids.append(user_pid)

    os.waitpid(library_pid, 0)
    for pid in user_pids:
        os.waitpid(pid, 0)