import socket

from scapy.layers.inet import IP


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP) as s:
        s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
        s.bind(('127.0.0.1', 5064))
        while True:
            d, a = s.recvfrom(1035)
            print(a)
            IP(d).show2()
