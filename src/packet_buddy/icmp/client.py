import socket

from scapy.layers.inet import IP, IPOption_NOP, UDP


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP) as s:
        s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
        # s.sendto(bytes(IP(dst='127.0.0.1', options=[IPOption_NOP()]) / ICMP(type=3, code=1)), ('127.0.0.1', 0))
        s.sendto(bytes(IP(dst='127.0.0.1', options=[IPOption_NOP()]) / UDP(sport=5603, dport=5604)), ('127.0.0.1', 0))
