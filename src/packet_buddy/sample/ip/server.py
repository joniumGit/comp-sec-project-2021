import socket

from ...messagers import IPDecoder


def handle_connection(s: socket.socket):
    import time
    decoder = IPDecoder()
    try:
        buffer = bytes()
        count = 88
        while True:
            r = s.recv(1024)
            count -= 1
            if r == b'':
                break
            else:
                buffer += r
                time.sleep(0.001)
                if count == 0:
                    break
        print("Received message:")
        print(decoder(buffer).decode('utf-8'))
    except Exception as e:
        print(repr(e.args))


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP) as s:
        s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
        s.bind(('127.0.0.1', 5064))
        handle_connection(s)
