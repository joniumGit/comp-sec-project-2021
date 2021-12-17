import time
from threading import Thread

from .ip import IPMessager
from .message import message, Data

SECRET = b'super duper secret key! Encrypt!'


class ST(Thread):

    def run(self) -> None:
        s = IPMessager[Data](2, SECRET)
        s.receive(lambda d: print(d.payload.json()))


server = ST()
server.daemon = True
server.start()

time.sleep(1)

m = IPMessager[Data](1, SECRET)
m.message[message('a', 'b', 'hello')] >> ('127.0.0.1', IPMessager.DUMMY_UDP)

time.sleep(1)
