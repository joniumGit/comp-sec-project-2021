import socket

from scapy.all import StreamSocket, Raw

from ...messagers import *


def connect(host: str) -> StreamSocket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, 5604))
    return StreamSocket(sock, Raw)


def main(dest: str, message: str):
    ss = connect(dest)
    ipm = IPMessager(dest)
    message = ipm(message.encode('utf-8'))
    for p in message:
        ss.send(p)
    ss.close()
