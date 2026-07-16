import os
import socket
import sys
import threading

from celery.__main__ import main


def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    s.listen(5)

    def run():
        while True:
            try:
                c, a = s.accept()
                c.recv(1024)
                c.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
                c.close()
            except Exception:
                break

    t = threading.Thread(target=run, daemon=True)
    t.start()
    print(f"Health server started on port {port}")

if __name__ == "__main__":
    start_health_server()
    sys.argv = [
        "celery",
        "-A",
        "src.core.celery_app",
        "worker",
        "--loglevel=info",
        "--concurrency=2"
        ]
    main()
