from .interface import *
from .utils import *




class ICMPMessager(TypedMessager, Generic[PT]):

    def send(self, m: Message):
        data = bytes(m)
        ts = 10

        def send(d: bytes):
            with make_socket() as s:
                s.sendto(
                    bytes(
                        IP(
                            dst=m.target[0],
                            options=[
                                IPOption_Timestamp(flg=0, timestamp=ts)
                            ]
                        )
                        / ICMP(type=0)
                        / d
                    ),
                    m.target
                )

        while len(data) > 60000:
            out = data[:60000]
            data = data[60000:]
            send(out)
            ts += 1

        ts = 9
        send(data)

    def receive(self, callback: Callable[[Message[PT]], NoReturn]):
        data = {}
        while True:
            with make_socket() as s:
                data, _, _, addr = s.recvmsg(PACKET_MAX)
