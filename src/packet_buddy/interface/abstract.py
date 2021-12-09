import logging
import socket
import time
from abc import abstractmethod, ABC
from queue import Queue, Empty
from threading import Lock
from threading import Thread, Event
from typing import Callable, List

from pydantic import BaseModel

from .interfaces import Client, Server, MessageContainer, MT, PACKET_MAX


class BasicMessage(BaseModel):
    message: str
    verifier: str


class ProtocolFilter(ABC):

    @abstractmethod
    def __call__(self, data: bytes) -> bool:
        pass


class ProtocolReverseAdapter(ABC):

    def is_eom(self, data: bytes) -> bool:
        return True

    @abstractmethod
    def __call__(self, message: List[bytes], wrapper: MessageContainer[MT]) -> MessageContainer[MT]:
        pass


class ProtocolAdapter(ABC):

    @abstractmethod
    def __call__(self, message: MessageContainer[MT]) -> List[bytes]:
        pass

    @abstractmethod
    def __invert__(self) -> 'ProtocolReverseAdapter':
        pass


class TaskBase(Thread):

    def __init__(
            self,
            _socket: socket.socket,
            queue: Queue,
            message_provider: Callable,
            message_converter: ProtocolAdapter,
            log: logging.Logger,
            kill_event: Event
    ):
        super(TaskBase, self).__init__(daemon=True)
        self.queue = queue
        self.socket = _socket
        self.msg = message_provider
        self.converter = message_converter
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

    def action(self):
        try:
            message = self.queue.get(block=True)
            self.log.debug("Message Send Event")
            for packet in self.converter(message):
                self.socket.sendto(packet, (message.ip, message.port))
        except Exception as e:
            self.log.exception("Sender killed", exc_info=e)
            raise e


class Receiver(TaskBase):
    converter: ProtocolReverseAdapter

    def __init__(self, _filter: ProtocolFilter, *args):
        super(Receiver, self).__init__(*args)
        self._filter = _filter
        self.data_store = dict()

    def receive(self) -> MessageContainer[MT]:
        ds = self.data_store
        while not self._kill.is_set():
            data, _, _, addr = self.socket.recvmsg(PACKET_MAX)
            if self._filter(data):
                self.log.debug("Message Receive Event")
                if addr not in ds:
                    ds[addr] = [list(), time.time()]
                ds[addr][0].append(data)
                ds[addr][1] = time.time()
                if self.converter.is_eom(data):
                    try:
                        return self.converter(ds.pop(addr)[0], self.msg() << addr)
                    finally:
                        to_remove = list()
                        for k in ds:
                            if time.time() - ds[k][1] > 10:
                                to_remove.append(k)
                        for k in to_remove:
                            ds.pop(k)

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

    def __init__(self, /, protocol: ProtocolAdapter, _filter: ProtocolFilter):
        self.tl = Lock()
        self._kill = Event()
        self.protocol = protocol
        self._filter = _filter
        self.__sender = None
        self.__receiver = None

    @abstractmethod
    def new_message(self):
        pass

    @abstractmethod
    def new_socket(self):
        pass

    def start(self):
        self.send_queue = Queue(self.queue_size)
        self.recv_queue = Queue(self.queue_size)

        self.__sender = Sender(
            self.new_socket(),
            self.send_queue,
            self.new_message,
            self.protocol,
            self.log,
            self._kill
        )
        self.__receiver = Receiver(
            self._filter,
            self.new_socket(),
            self.recv_queue,
            self.new_message,
            ~self.protocol,
            self.log,
            self._kill
        )

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
    def __init__(self, /, protocol: ProtocolAdapter, _filter: ProtocolFilter):
        super().__init__(protocol, _filter)

    def new_message(self):
        return super(Client, self).new_message()


class AbstractServer(AbstractTasker, Server):
    log = logging.getLogger('Server')

    @abstractmethod
    def __init__(self, /, protocol: ProtocolAdapter, _filter: ProtocolFilter):
        super().__init__(protocol, _filter)

    def new_message(self):
        return super(Server, self).new_message()

    def handle_connection(self):
        pass


__all__ = ['AbstractClient', 'AbstractServer', 'ProtocolAdapter', 'ProtocolReverseAdapter', 'BasicMessage',
           'ProtocolFilter']
