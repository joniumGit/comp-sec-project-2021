import socket

from pydantic import BaseModel


class BasicMessage(BaseModel):
    message: str
    verifier: str


def make_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
    return s
