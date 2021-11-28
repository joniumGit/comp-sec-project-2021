import socket

from ...messagers import IPDecoder


def handle_connection(s: socket.socket):
    import time
    decoder = IPDecoder()
    try:
        buffer = bytes()
        while True:
            r = s.recv(4096)
            if r == b'':
                break
            else:
                buffer += r
                time.sleep(0.001)
        print("Received message:")
        print(decoder(buffer).decode('utf-8'))
    except Exception as e:
        print(repr(e.args))


def main():
    with socket.create_server(
            ('', 5604),
            family=socket.AF_INET,
            backlog=10,
    ) as sock:
        while True:
            recv, addr = sock.accept()
            try:
                if recv is not None:
                    handle_connection(recv)
            finally:
                recv.close()
                break
