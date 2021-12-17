import socket
import time

from scapy.layers.inet import IP, UDP

from .interface import *
from .ip_utils import *
from .utils import *


class IPMessager(TypedMessager, Generic[PT]):
    DUMMY_UDP = 8521
    PACKET = PACKET_MAX
    CLEAN_TIME = 5

    def __init__(self, _id: int, secret: bytes):
        self.id = _id
        self.secret = secret
        self.data_cache = {}

    def send(self, m: Message[PT]):
        with make_socket(socket.IPPROTO_UDP) as s:
            for part in Shifter.encode_message(bytes(m), self.id, bytes_per_option=16, secret=self.secret):
                s.sendto(
                    bytes(
                        IP(
                            dst=m.target[0],
                            options=part
                        ) / UDP(sport=IPMessager.DUMMY_UDP, dport=IPMessager.DUMMY_UDP)
                    ),
                    m.target
                )

    def _receive(self, addr: Tuple, data: bytes, callback: Callable[[Message[PT]], NoReturn]):
        d = data.rstrip(b'\x00')
        m = self.message[d]
        m.target = addr
        callback(m)

    def _clean(self):
        rem = list()
        for k, v in self.data_cache.items():
            if time.time() - v > IPMessager.CLEAN_TIME:
                rem.append(k)
        for k in rem:
            self.data_cache.pop(k)

    def receive(self, callback: Callable[[Message[PT]], NoReturn]):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as dummy:
            dummy.bind(('0.0.0.0', IPMessager.DUMMY_UDP))
            cleaned_at = time.time()
            with make_socket(socket.IPPROTO_UDP) as s:
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
                                self._receive(
                                    addr,
                                    Shifter.decode_message(self.data_cache.pop(tid)[0], secret=self.secret),
                                    callback
                                )
                        if time.time() - cleaned_at > IPMessager.CLEAN_TIME:
                            self._clean()
                    except Exception as e:
                        raise e
                        pass


__all__ = ['IPMessager']
