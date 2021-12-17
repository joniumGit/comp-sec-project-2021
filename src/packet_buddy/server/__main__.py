from ..base import IPMessager, Data, Message

m = IPMessager[Data](69, b'super duper secret key! Encrypt!', 16, protocol='icmp-pl')


def on_message(message: Message):
    m.message[Data(sender="server", topic="server reply", content=message.payload.content)] >> message.target


m.receive(on_message)
