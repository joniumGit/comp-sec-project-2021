import time
from threading import Thread

from . import client
from . import server


class Server(Thread):

    def run(self) -> None:
        super().run()
        print("Server starting...")
        server.main()


class Client(Thread):

    def run(self) -> None:
        super().run()
        print("Client starting...")
        client.main()


server_thread = Server()
client_thread = Client()

server_thread.start()
time.sleep(0.1)
client_thread.start()
time.sleep(0.5)
