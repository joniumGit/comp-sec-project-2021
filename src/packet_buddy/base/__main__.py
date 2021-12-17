import sys
import time
from threading import Thread

from .ip import IPMessager
from .message import message, Data

SECRET = b'super duper secret key! Encrypt!'


# Well, this is bad
# https://www.stigviewer.com/stig/cisco_ios_router_rtr/2020-06-30/finding/V-96637
# https://www2.eecs.berkeley.edu/Pubs/TechRpts/2005/EECS-2005-24.pdf

class ST(Thread):

    def run(self) -> None:
        s = IPMessager[Data](2, SECRET, 24, 'icmp-pl')

        def on_message(d):
            print(d.payload.json())
            d.payload.sender = "b"
            s.message[message("server", "Server Hello", d.payload.content)] >> d.target

        s.receive(on_message)


server = ST()
server.daemon = True
server.start()

time.sleep(1)

m = IPMessager[Data](1, SECRET, 64, 'icmp-pl')
m.message[message('a', 'b', 'hello')] >> ('127.0.0.1', IPMessager.DUMMY_UDP)


def on_message(d):
    print(d.payload.json())
    sys.exit()


m.receive(on_message)

time.sleep(1)
