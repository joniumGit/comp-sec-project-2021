import time
from threading import Thread

from . import crafter
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
        message = "Hello, 你好. This is a hidden message. \nHope everything is well"
        print(f"Message:\n{message}")
        crafter.main(
            dest='127.0.0.1',
            message=message
        )


server_thread = Server()
client_thread = Client()

server_thread.start()
time.sleep(0.1)
client_thread.start()
time.sleep(0.5)
