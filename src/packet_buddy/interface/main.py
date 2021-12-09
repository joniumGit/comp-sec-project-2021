from pydantic import BaseModel

from messager import MessageContainer


class Data(BaseModel):
    number: int
    name: str


incoming = Data(number=123, name="hello world").json().encode('utf-8')
message = MessageContainer[Data]
message2 = MessageContainer[Data]
message = MessageContainer[Data] << incoming
print(message.payload.json())
