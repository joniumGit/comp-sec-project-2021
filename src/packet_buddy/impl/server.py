import logging
import socket
from typing import Callable

from scapy.layers.inet import IP, ICMP, IPOption_NOP

from .common import make_socket
from ..interface import Server, MessageContainer, MT, PACKET_MAX


class ICMPServer(Server):
    server_socket: socket.socket

    def __init__(self, /, processor: Callable[[MessageContainer[MT]], None] = lambda a: None):
        self.processor = processor
        self.log = logging.getLogger('ICMPServer')

    def start(self):
        self.server_socket = make_socket()

    def stop(self):
        self.server_socket.close()

    def handle_connection(self):
        pass

    def send_message(self, message: MessageContainer[MT]):
        self.log.debug("Sending Message")
        self.server_socket.sendto(
            bytes(IP(dst=message.ip, options=[IPOption_NOP()]) / ICMP(type=0) / ~message),
            (message.ip, message.port)
        )

    def receive_message(self):
        while True:
            data, _, _, addr = self.server_socket.recvmsg(PACKET_MAX)
            try:
                p = IP(data)
                if len(p.options) == 0:
                    self.log.debug("Received Message")
                    m = self.new_message()
                    m << addr
                    m << p.lastlayer().load
                    if self.log.level == logging.DEBUG:
                        self.log.debug(m)
                    self.processor(m)
                    self.send_message(m)
            except:
                pass
