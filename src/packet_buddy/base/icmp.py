import socket

from scapy.layers.inet import IP, ICMP

from .interface import *
from .utils import *


def wrap(target: str, data: bytes):
    return bytes(
        IP(dst=target)
        / ICMP(type=0)
        / data
    )


class ICMPMessager(TypedMessager, Generic[PT]):

    def send(self, m: Message[PT]):
        data = m.payload.json().encode('utf-8')
        with make_socket(socket.IPPROTO_ICMP) as s:
            while len(data) > 60000:
                out = data[:60000]
                data = data[60000:]
                s.sendto(wrap(m.target[0], out), m.target)
            s.sendto(wrap(m.target[0], out), m.target)

    def receive(self, callback: Callable[[Message[PT]], NoReturn]):
        data = {}
        while True:
            with make_socket(socket.IPPROTO_ICMP) as s:
                data, _, _, addr = s.recvmsg(PACKET_MAX)
