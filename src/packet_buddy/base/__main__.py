import time
from threading import Thread

from .encoding import IPMessager
from .message import message, Data


class ST(Thread):

    def run(self) -> None:
        s = IPMessager[Data](2)
        s.receive(lambda d: print(d.payload.json()))


server = ST()
server.daemon = True
server.start()

time.sleep(1)

m = IPMessager[Data](1)
m.message[message('a', 'b', 'hello')] >> ('127.0.0.1', IPMessager.DUMMY_UDP)

time.sleep(1)
