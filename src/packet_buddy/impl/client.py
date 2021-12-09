from queue import Queue, Empty
from threading import Lock

from .tasks import Sender, Receiver
from ..interface import MessageContainer, MT, Client


class ICMPClient(Client):

    def __init__(self):
        self.server_ip = '127.0.0.1'
        self.send_queue = Queue(1000)
        self.recv_queue = Queue(1000)
        self.tl = Lock()

    def new_message(self) -> MessageContainer[MT]:
        if self.tl.acquire(blocking=True):
            try:
                return super().new_message()
            finally:
                self.tl.release()

    def start(self):
        self.__sender = Sender(self.send_queue, self.new_message)
        self.__receiver = Receiver(self.recv_queue, self.new_message)

        self.__sender.start()
        self.__receiver.start()

    def stop(self):
        try:
            self.__sender.kill()
        finally:
            self.__receiver.kill()

    def send_message(self, message: MessageContainer[MT]):
        if message.ip is None:
            message.ip = self.server_ip
            message.port = 23
        self.send_queue.put(message, block=True)

    def receive_message(self) -> MessageContainer[MT]:
        try:
            return self.recv_queue.get(block=False)
        except Empty:
            return None
