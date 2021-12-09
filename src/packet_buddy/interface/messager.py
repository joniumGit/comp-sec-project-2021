from abc import abstractmethod, ABC
from typing import Generic, TypeVar, Dict, Tuple, Any, Type, cast, Union, Optional

from pydantic import BaseModel

MT = TypeVar('MT', bound=BaseModel)
PACKET_MAX = 65535


class Wrapper:
    """
    Helper for producing messages with preset deserializers
    """
    __slots__ = ['actual_class', 'generic_type']

    def __init__(self, actual_class, generic_type):
        self.generic_type = generic_type
        self.actual_class = actual_class

    def __call__(self, *args, **kwargs):
        """
        Wraps the actual instance creation and sets the payload to the desired generic type

        :param args:   Class args
        :param kwargs: Class args
        :return:       Instance
        """
        instance = self.actual_class(*args, **kwargs)
        instance._type = self.generic_type
        return instance

    def __class_getitem__(cls, item: Tuple[MT, Any]) -> MT:
        """
        This is made to prevent double wrapping

        :param item:    Tuple of a generic type wrapper and the caught runtime type
        :return:        Class Instance
        """
        wrapper, runtime_type = item
        if not isinstance(wrapper.__origin__, Wrapper):
            wrapper.__origin__ = Wrapper(wrapper.__origin__, runtime_type)
        return wrapper


class MessageContainer(Generic[MT]):
    __slots__ = ['ip', 'port', 'payload', '_type']
    ip: Optional[str]
    port: Optional[int]
    payload: Union[bytes, MT, None]
    _type: Type[MT]

    def __init__(self, /, _type=None):
        if _type is not None:
            self._type = _type
        self.port = None
        self.ip = None
        self.payload = None

    def __class_getitem__(cls, generic_runtime_type) -> 'MessageContainer[MT]':
        """
        Handles invocations like:

        with ICMPServer[BasicMessage]() as server:
            ...

        Where type information can be intercepted.

        :param generic_runtime_type: This is what is called in Generic types
        :return:                     A modified generic type-wrapper that will produce an actual instance
        """
        return cast(
            'MessageContainer[MT]',
            Wrapper[super(MessageContainer, cls).__class_getitem__(generic_runtime_type), generic_runtime_type]()
        )

    def __lshift__(self, other: Union[bytes, MT, Tuple[str, int]]) -> 'MessageContainer[MT]':
        if isinstance(other, Tuple):
            self.ip, self.port = other
        elif isinstance(other, bytes):
            self.payload = self._type.parse_raw(other)
        else:
            self.payload = other
        return self

    def __invert__(self) -> bytes:
        return self.payload.json().encode('utf-8') if self.payload is not None else b''

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        data = [
            self.ip if hasattr(self, 'ip') else None,
            self.port if hasattr(self, 'port') else None,
            self.payload if hasattr(self, 'payload') else None,
        ]
        return f"MessageContainer({data[0]}, {data[1]}, {data[2] if data[2] is None else data[2].json()})"


class BaseClass(ABC):
    _type: Type[MT]

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __class_getitem__(cls, message_type) -> Type[MT]:
        """
        Handles invocations like:

        with ICMPServer[BasicMessage]() as server:
            ...

        Where type information can be intercepted.

        :param message_type: The message type to handle
        :return:             An initializer
        """

        def instantiate(*args, **kwargs):
            i = cls(*args, **kwargs)
            i._type = message_type
            return i

        return instantiate

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    def new_message(self) -> MessageContainer[MT]:
        return MessageContainer(_type=self._type)

    @abstractmethod
    def send_message(self, message: MessageContainer[MT]):
        pass

    @abstractmethod
    def receive_message(self) -> MessageContainer[MT]:
        pass


class Client(BaseClass):
    server_ip: str
    port: int


class Server(BaseClass):
    connections: Dict

    @abstractmethod
    def handle_connection(self):
        pass


__all__ = ['Client', 'Server', 'MessageContainer', 'MT', 'BaseModel', 'PACKET_MAX']
