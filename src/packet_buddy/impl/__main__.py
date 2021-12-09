import time
from threading import Thread

from . import ICMPClient, ICMPServer, BasicMessage
from ..interface import MessageContainer


class Server(Thread):

    def run(self) -> None:
        super().run()
        print("Server starting...")

        def processor(m: MessageContainer[BasicMessage]):
            if m.payload.message[-1] == 'd':
                m.payload.message += " 1"
            else:
                split = m.payload.message.rsplit(' ', maxsplit=1)
                m.payload.message = split[0] + f" {int(split[-1]) + 1}"

        with ICMPServer[BasicMessage](processor=processor) as server:
            server.receive_message()


class Client(Thread):

    def run(self) -> None:
        super().run()
        print("Client starting...")
        with ICMPClient[BasicMessage]() as client:
            m = client.new_message()
            m << BasicMessage(message="Hello World", verifier="lol")
            while True:
                client.send_message(m)
                while True:
                    resp = client.receive_message()
                    if resp is None:
                        continue
                    else:
                        m = resp
                        break


server_thread = Server()
client_thread = Client()

server_thread.start()
time.sleep(0.1)
client_thread.start()
time.sleep(0.5)
