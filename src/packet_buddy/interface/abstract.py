import logging
import socket
from abc import abstractmethod, ABC
from queue import Queue, Empty
from threading import Lock
from threading import Thread, Event
from typing import Callable

from pydantic import BaseModel

from ..interface import Client, Server
from ..interface import MessageContainer, MT, PACKET_MAX


class BasicMessage(BaseModel):
    message: str
    verifier: str


def make_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
    return s


class ProtocolReverseAdapter(ABC):

    @abstractmethod
    def __call__(self, message: bytes, wrapper: MessageContainer[MT]) -> MessageContainer[MT]:
        pass

    @abstractmethod
    def __invert__(self) -> 'ProtocolAdapter':
        pass


class ProtocolAdapter(ABC):

    @abstractmethod
    def __call__(self, message: MessageContainer[MT]) -> bytes:
        pass

    @abstractmethod
    def __invert__(self) -> 'ProtocolReverseAdapter':
        pass


class TaskBase(Thread):

    def __init__(
            self,
            queue: Queue,
            message_provider: Callable,
            message_converter: ProtocolAdapter,
            log: logging.Logger,
            kill_event: Event
    ):
        super(TaskBase, self).__init__(daemon=True)
        self.queue = queue
        self.socket = make_socket()
        self.msg = message_provider
        self.convert = message_converter
        self._kill = kill_event
        self.log = log

    @abstractmethod
    def action(self):
        pass

    def run(self) -> None:
        try:
            while not self._kill.is_set():
                self.action()
        except:
            pass
        finally:
            self.cleanup()

    def kill(self):
        self._kill.set()

    def cleanup(self):
        try:
            old = self.queue
            self.queue = Queue()
            i = old.get(block=True, timeout=0.01)
            while i is not None:
                self.queue.put(i, block=True)
                self.action()
                i = old.get_nowait()
            self.queue = old
        except:
            pass
        finally:
            self.socket.close()


class Sender(TaskBase):

    def send(self, message: MessageContainer[MT]):
        self.log.debug("Sending Message")
        self.socket.sendto(
            self.convert(message),
            (message.ip, message.port)
        )

    def action(self):
        try:
            self.send(self.queue.get(block=True))
        except Exception as e:
            self.log.exception("Sender killed", exc_info=e)
            raise e


class Receiver(TaskBase):

    def __init__(self, *args, **kwargs):
        super(Receiver, self).__init__(*args, **kwargs)
        self.convert = ~self.convert

    def receive(self) -> MessageContainer[MT]:
        while not self._kill.is_set():
            data, _, _, addr = self.socket.recvmsg(PACKET_MAX)
            try:
                m = self.convert(data, self.msg() << addr)
                if m is not None:
                    return m
            except:
                pass

    def action(self) -> None:
        try:
            self.queue.put(self.receive(), block=True)
        except Exception as e:
            self.log.exception("Receiver killed", exc_info=e)
            raise e


class AbstractTasker(ABC):
    send_queue: Queue
    recv_queue: Queue
    queue_size: int = 1000
    log: logging.Logger = None

    def __init__(self, /, protocol: ProtocolAdapter):
        self.tl = Lock()
        self._kill = Event()
        self.protocol = protocol
        self.__sender = None
        self.__receiver = None

    @abstractmethod
    def new_message(self):
        pass

    def start(self):
        self.send_queue = Queue(self.queue_size)
        self.recv_queue = Queue(self.queue_size)

        self.__sender = Sender(self.send_queue, self.new_message, self.protocol, self.log, self._kill)
        self.__receiver = Receiver(self.recv_queue, self.new_message, self.protocol, self.log, self._kill)

        self.__sender.start()
        self.__receiver.start()

    def stop(self):
        self._kill.set()
        try:
            self.__sender.kill()
        finally:
            self.__receiver.kill()
        try:
            self.__sender.join()
        except:
            pass

    def send_message(self, message: MessageContainer[MT]):
        self.send_queue.put(message, block=True)

    def receive_message(self) -> MessageContainer[MT]:
        try:
            return self.recv_queue.get(block=False)
        except Empty:
            return None

    @abstractmethod
    def handle_message(self, message: MessageContainer[MT]):
        pass

    def serve(self):
        while not self._kill.is_set():
            m = self.receive_message()
            if m is not None:
                self.handle_message(m)


class AbstractClient(AbstractTasker, Client):
    log = logging.getLogger('Client')

    @abstractmethod
    def __init__(self, /, protocol: ProtocolAdapter):
        super().__init__(protocol)

    def new_message(self):
        return super(Client, self).new_message()


class AbstractServer(AbstractTasker, Server):
    log = logging.getLogger('Server')

    @abstractmethod
    def __init__(self, /, protocol: ProtocolAdapter):
        super().__init__(protocol)

    def new_message(self):
        return super(Server, self).new_message()

    def handle_connection(self):
        pass


__all__ = ['AbstractClient', 'AbstractServer', 'ProtocolAdapter', 'ProtocolReverseAdapter', 'BasicMessage']
