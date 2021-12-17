import base64
import hmac
from typing import cast

from pydantic import Field

from .interface import *

HMAC = hmac.HMAC(b"super duper secret", digestmod='sha512')


def to_verifier(data: 'DefaultMessageModel') -> str:
    h = HMAC.copy()
    h.update(data.json(exclude={"verifier"}).encode('utf-8'))
    return base64.b64encode(h.digest(), altchars=b'-_').decode('ascii')


def verify(m: 'Data') -> bool:
    try:
        return hmac.compare_digest(to_verifier(m.data), m.verifier)
    except Exception as e:
        raise e
        return False


class BadMessage(Exception):
    pass


class DefaultMessageModel(BaseModel):
    sender: str = Field(alias='from')
    topic: str = Field(alias='to')
    content: str

    class Config:
        allow_population_by_field_name = True


class Data(BaseModel):
    data: DefaultMessageModel
    verifier: str = ""

    @classmethod
    def parse_raw(cls, *args, **kwargs) -> 'Data':
        o = cast(Data, super(Data, cls).parse_raw(*args, **kwargs))
        print(o.json())
        if isinstance(o, Data) and verify(o):
            return o
        else:
            raise BadMessage()

    def json(self, *args, **kwargs):
        self.verifier = to_verifier(self.data).strip()
        return super(Data, self).json(*args, **kwargs)


def message(_from: str, topic: str, content: str) -> Data:
    return Data(data=DefaultMessageModel(sender=_from, topic=topic, content=content))


__all__ = [
    'BadMessage',
    'Data',
    'DefaultMessageModel',
    'message',
]
