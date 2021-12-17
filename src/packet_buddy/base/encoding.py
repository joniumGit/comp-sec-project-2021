import socket
import time
from typing import Tuple

from scapy.layers.inet import IP, ICMP, IPOption_Timestamp, UDP

from .flags import *
from .interface import *

CLEAN_TIME = 5


def get_payload(packet: IP) -> int:
    return packet.options[0].timestamp


def make_socket(protocol: int = socket.IPPROTO_ICMP):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, protocol)
    s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
    return s


class IPMessager(TypedMessager, Generic[PT]):
    DUMMY_UDP = 8521
    PACKET = PACKET_MAX

    def __init__(self, _id: int):
        self.id = _id
        self.data_cache = {}

    def send(self, m: Message[PT]):
        with make_socket(socket.IPPROTO_UDP) as s:
            for part in Shifter.encode_message(bytes(m), self.id):
                s.sendto(
                    bytes(
                        IP(
                            dst=m.target[0],
                            options=timestamp(part.to_bytes(4, byteorder='big', signed=False))[0] # [IPOption_Timestamp(flg=0, timestamp=part)]
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
            if time.time() - v > CLEAN_TIME:
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
                        packet: IP = IP(_raw_bytes)
                        try:
                            ts = packet.options[0]
                        except:
                            continue
                        tid = (Shifter.get_id(ts), *addr)
                        if Shifter.is_start(ts):
                            sender = Shifter.get_id(ts)
                            print(sender)
                            if sender != self.id:
                                self.data_cache[tid] = [ts], time.time()
                        if tid in self.data_cache:
                            d = self.data_cache.pop(tid)[0]
                            d.append(ts)
                            self.data_cache[tid] = d, time.time()
                            if Shifter.is_end(ts):
                                self._receive(
                                    addr,
                                    Shifter.decode_message(self.data_cache.pop(tid)[0]),
                                    callback
                                )
                        if time.time() - cleaned_at > CLEAN_TIME:
                            self._clean()
                    except Exception as e:
                        raise e
                        pass


class ICMPMessager(TypedMessager, Generic[PT]):

    def send(self, m: Message):
        data = bytes(m)
        ts = 10

        def send(d: bytes):
            with make_socket() as s:
                s.sendto(
                    bytes(
                        IP(
                            dst=m.target[0],
                            options=[
                                IPOption_Timestamp(flg=0, timestamp=ts)
                            ]
                        )
                        / ICMP(type=0)
                        / d
                    ),
                    m.target
                )

        while len(data) > 60000:
            out = data[:60000]
            data = data[60000:]
            send(out)
            ts += 1

        ts = 9
        send(data)

    def receive(self, callback: Callable[[Message[PT]], NoReturn]):
        data = {}
        while True:
            with make_socket() as s:
                data, _, _, addr = s.recvmsg(PACKET_MAX)



__all__ = ['ICMPMessager', 'IPMessager']
