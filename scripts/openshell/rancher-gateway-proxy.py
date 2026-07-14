import socket
import threading

LISTEN = ("0.0.0.0", 17670)
TARGET = ("host.rancher-desktop.internal", 17670)


def close(sock):
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        sock.close()
    except OSError:
        pass


def pump(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    finally:
        close(src)
        close(dst)


def handle(client, addr):
    try:
        upstream = socket.create_connection(TARGET, timeout=10)
        client.settimeout(None)
        upstream.settimeout(None)
        threading.Thread(target=pump, args=(client, upstream), daemon=True).start()
        pump(upstream, client)
    except Exception as exc:
        print(f"proxy error from {addr}: {exc!r}", flush=True)
        close(client)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(LISTEN)
server.listen(128)
print(f"forwarding {LISTEN[0]}:{LISTEN[1]} -> {TARGET[0]}:{TARGET[1]}", flush=True)

while True:
    client, addr = server.accept()
    threading.Thread(target=handle, args=(client, addr), daemon=True).start()
