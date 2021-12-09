import logging
from queue import Queue
from threading import Thread, Event

from scapy.layers.inet import IP, ICMP

from .common import make_socket
from ..interface import MessageContainer, MT, PACKET_MAX


class TaskBase(Thread):

    def __init__(self, queue: Queue, message_provider):
        super(TaskBase, self).__init__()
        self.queue = queue
        self.socket = make_socket()
        self.msg = message_provider
        self._kill = Event()

        self.log = logging.getLogger('ICMPClient')

    def kill(self):
        try:
            self._kill.set()
        finally:
            self.socket.close()


class Sender(TaskBase):

    def send(self, message: MessageContainer[MT]):
        self.log.debug("Sending Message")
        self.socket.sendto(
            bytes(IP(dst=message.ip) / ICMP(type=0) / ~message),
            (message.ip, message.port)
        )

    def run(self) -> None:
        try:
            while not self._kill.is_set():
                self.send(self.queue.get(block=True))
        except Exception as e:
            self.log.exception("Sender killed", exc_info=e)


class Receiver(TaskBase):

    def receive(self) -> MessageContainer[MT]:
        while not self._kill.is_set():
            data, _, _, addr = self.socket.recvmsg(PACKET_MAX)
            try:
                p = IP(data)
                if p.options[0].option == 1:
                    from logging import getLogger
                    self.log.debug(f"Received Message From: {addr[0]}")
                    m = self.msg()
                    m << addr
                    m << p.lastlayer().load
                    return m
            except:
                pass

    def run(self) -> None:
        try:
            while not self._kill.is_set():
                self.queue.put(self.receive(), block=True, timeout=None)
        except Exception as e:
            self.log.exception("Receiver killed", exc_info=e)
