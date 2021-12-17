import socket
import time

from scapy.layers.inet import IP, UDP, ICMP

from .interface import *
from .ip_utils import *
from .utils import *


def udp_wrap(target: str, data: bytes):
    return bytes(
        IP(
            dst=target,
            options=data
        ) / UDP(sport=IPMessager.DUMMY_UDP, dport=IPMessager.DUMMY_UDP)
    )


def icmp_wrap(target: str, data: bytes):
    return bytes(
        IP(
            dst=target,
            options=data
        ) / ICMP(type=3, code=3)
    )


class IPMessager(TypedMessager, Generic[PT]):
    DUMMY_UDP = 8521
    PACKET = PACKET_MAX
    CLEAN_TIME = 5

    def __init__(
            self,
            _id: int,
            secret: bytes,
            bpo: int,
            protocol: int = socket.IPPROTO_UDP,
    ):
        self.id = _id
        self.secret = secret
        if not (3 < bpo < 33 and bpo % 4 == 0):
            raise ValueError()
        self.bpo = bpo
        self.protocol = protocol
        self.wrap = udp_wrap if protocol == socket.IPPROTO_UDP else icmp_wrap
        self.data_cache = {}

    def send(self, m: Message[PT]):
        with make_socket(self.protocol) as s:
            for part in Shifter.encode_message(bytes(m), self.id, bytes_per_option=self.bpo, secret=self.secret):
                s.sendto(self.wrap(m.target[0], part), m.target)

    def clean(self):
        rem = list()
        for k, v in self.data_cache.items():
            if time.time() - v > IPMessager.CLEAN_TIME:
                rem.append(k)
        for k in rem:
            self.data_cache.pop(k)

    def receive(self, callback: Callable[[Message[PT]], NoReturn]):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as dummy:
            try:
                if self.protocol == socket.IPPROTO_UDP:
                    dummy.bind(('0.0.0.0', IPMessager.DUMMY_UDP))
            except:
                pass
            cleaned_at = time.time()
            with make_socket(self.protocol) as s:
                while True:
                    _raw_bytes, _, _, addr = s.recvmsg(IPMessager.PACKET)
                    try:
                        ts = _raw_bytes[20:]
                        tid = (Shifter.get_id(ts), *addr)
                        if Shifter.is_start(ts):
                            sender = Shifter.get_id(ts)
                            if sender != self.id:
                                self.data_cache[tid] = [ts], time.time()
                        elif tid in self.data_cache:
                            d = self.data_cache.pop(tid)[0]
                            d.append(ts)
                            self.data_cache[tid] = d, time.time()
                            if Shifter.is_end(ts):
                                d = Shifter.decode_message(
                                    self.data_cache.pop(tid)[0],
                                    secret=self.secret
                                ).rstrip(b'\x00')
                                m = self.message[d]
                                m.target = addr
                                callback(m)
                        if time.time() - cleaned_at > IPMessager.CLEAN_TIME:
                            self.clean()
                    except Exception as e:
                        raise e
                        pass


__all__ = ['IPMessager']
