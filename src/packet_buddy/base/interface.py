from abc import abstractmethod, ABCMeta
from typing import TypeVar, Type, cast, Tuple, NewType, Generic, NoReturn, Union, Callable

from pydantic import BaseModel, parse_raw_as

PT = TypeVar('PT', bound=BaseModel)
ST = TypeVar('ST', bound='TypedMessager')

Target = NewType('Target', Tuple[str, int])


class _InitWrapper:
    __slots__ = ['_cls', '_type']

    def __init__(self, _cls: Type['ST'], _type: Type['PT']):
        self._cls = _cls
        self._type = _type

    def __call__(self, *args, **kwargs):
        inst = self._cls(*args, **kwargs)
        inst.__dict__['_message_type'] = self._type
        return inst


class Message(Generic[PT]):
    __slots__ = ['target', 'payload', '_payload_type', '_parent']

    target: Target
    payload: PT
    _payload_type: Type[PT]
    _parent: ST

    def __init__(self, parent: ST):
        self._parent = parent

    def __getitem__(self, payload_data: Union[bytes, BaseModel]) -> 'Message[PT]':
        if isinstance(payload_data, BaseModel):
            self.payload = payload_data
        else:
            self.payload = parse_raw_as(self._payload_type, payload_data)
        return self

    def __rshift__(self, target: Tuple[str, int]) -> NoReturn:
        self.target = Target(target)
        self._parent.send(self)

    def __bytes__(self) -> bytes:
        return self.payload.json().encode('utf-8')

    def __repr__(self):
        return f"Message{self.target}:\n{self.payload.json(indent=4) if self.payload is not None else 'no content'}"

    def __str__(self):
        return self.__repr__()


class TypedMessager(Generic[PT], metaclass=ABCMeta):
    _message_type: Type[PT]

    @property
    def message(self) -> Message[PT]:
        m = Message(self)
        m._payload_type = self._message_type
        return m

    def __class_getitem__(cls, message_type: Type[PT]) -> Type[ST]:
        return cast(
            Type['SB'],
            _InitWrapper(super(TypedMessager, cls).__class_getitem__(message_type), message_type)
        )

    @abstractmethod
    def send(self, m: Message[PT]):
        pass

    @abstractmethod
    def receive(self, callback: Callable[[Message[PT]], NoReturn]):
        pass


__all__ = [
    'Message',
    'TypedMessager',
    'BaseModel',
    'PT',
    'ST',
    # Typing
    'Generic',
    'Callable',
    'Type',
    'NoReturn'
]
