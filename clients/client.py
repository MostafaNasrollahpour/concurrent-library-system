import socket

MAIN_PORT = 5000  # همون پورت main server

def send_request(command):
    with socket.socket() as conn:
        conn.connect(('localhost', MAIN_PORT))
        conn.send(command.encode())
        resp = conn.recv(1024).decode()
        print(f"Response: {resp}")

# مثال استفاده
send_request("register_user NewUser")  # ثبت کاربر جدید، برگشت success <id> یا failure
send_request("register_book NewBook")  # اضافه کتاب
send_request("lend_book 1 NewBook")  # قرض (user_id رو از قبل بدون)
send_request("return_book 1 NewBook")  # پس دادن