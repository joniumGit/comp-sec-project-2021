import socket

from ...messagers import IPDecoder


def handle_connection(s: socket.socket):
    import time
    decoder = IPDecoder()
    buffer = bytes()
    count = 88
    while True:
        r = s.recv(1024)
        if r == b'':
            break
        else:
            count -= 1
            buffer += r
            time.sleep(0.001)
            if count == 0:
                break
    print("Received message:")
    print(decoder(buffer).decode('utf-8'))


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP) as s:
        s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
        s.bind(('127.0.0.1', 5004))
        handle_connection(s)
