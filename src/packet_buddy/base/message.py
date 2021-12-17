from pydantic import Field

from .interface import *


class Data(BaseModel):
    sender: str = Field(alias='from')
    topic: str = Field(alias='to')
    content: str

    class Config:
        allow_population_by_field_name = True


def message(_from: str, topic: str, content: str) -> Data:
    return Data(sender=_from, topic=topic, content=content)


__all__ = [
    'Data',
    'message',
]
