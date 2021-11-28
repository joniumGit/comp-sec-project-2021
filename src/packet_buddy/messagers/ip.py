from base64 import b64encode, b64decode
from typing import List

from scapy.layers.inet import IP, IPOption, TCP, IPOption_NOP, Packet

bitmap = [0x80, 0x40, 0x20, 0x10, 0x8, 0x4, 0x2, 0x1]


class IPMessager:

    def __init__(self, destination: str):
        self.dst = destination

    @staticmethod
    def byte_to_nop(byte: int) -> List[IPOption]:
        return [IPOption_NOP(copy_flag=i & byte != 0) for i in bitmap]

    @staticmethod
    def with_dummy_tcp(packet: IP) -> Packet:
        return packet / TCP(sport=5603, dport=5604)

    def nop_coded(self, data: bytes) -> List[IP]:
        dst = self.dst
        return [
            IPMessager.with_dummy_tcp(
                IP(
                    dst=dst,
                    options=IPMessager.byte_to_nop(byte)
                )
            ) for byte in data
        ]

    def __call__(self, message: bytes):
        return self.nop_coded(b64encode(message))


class IPDecoder:

    def __init__(self):
        pass

    @staticmethod
    def to_data(packets: List[Packet]) -> bytes:
        return b64decode(''.join(chr(int(''.join(str(o.copy_flag) for o in p.options), 2)) for p in packets))

    def __call__(self, data: bytes) -> bytes:
        buffer = data
        out = list()
        while True:
            try:
                p = IP(buffer)
                out.append(p)
                if not hasattr(p, 'load'):
                    break
                buffer = p.load
            except:
                break
        return IPDecoder.to_data(out)


__all__ = ['IPMessager', 'IPDecoder']
