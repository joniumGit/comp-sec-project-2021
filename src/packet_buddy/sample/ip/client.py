import socket

from ...messagers import *


def main(dest: str, message: str):
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP) as s:
        s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
        ipm = IPMessager(dest)
        message = ipm(message.encode('utf-8'))
        for p in message:
            s.sendto(bytes(p), (dest, 0))
        s.close()
