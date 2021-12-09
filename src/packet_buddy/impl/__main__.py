import time
from threading import Thread

from . import ICMPClient as ClientBase, ICMPServer as ServerBase, BasicMessage
from ..interface import L_COMMON, set_level, logging

CONVERSTION = ['Hello Server', 'Hello Client', 'Exchange Data?', 'Yes', 'Got It?', 'All Of It', 'OK', 'EXIT']
TEST_MESSAGES = {k: v for k, v in zip(CONVERSTION[:-1], CONVERSTION[1:])}
log = logging.getLogger(L_COMMON)
set_level(logging.INFO)


class IMPL:
    def handle_message(self, message):
        try:
            self.log.info(f"Received: {message}")
            message.payload.message = TEST_MESSAGES[message.payload.message]
            self.send_message(message)
        except KeyError:
            self.log.info('Done')
            self.send_queue.put(message, block=True)
            self.stop()


class ICMPClient(IMPL, ClientBase):
    pass


class ICMPServer(IMPL, ServerBase):
    pass


class Server(Thread):

    def run(self) -> None:
        super().run()
        log.info("Server starting...")
        with ICMPServer[BasicMessage]() as server:
            self._kill = server._kill
            server.serve()
        log.info("Server exiting...")


class Client(Thread):

    def run(self) -> None:
        super().run()
        log.info("Client starting...")
        with ICMPClient[BasicMessage]() as client:
            self._kill = client._kill
            m = client.new_message()
            m << BasicMessage(message=CONVERSTION[0], verifier="lol")
            client.send_message(m)
            client.serve()
        log.info("Client exiting...")


server_thread = Server(daemon=True)
client_thread = Client(daemon=True)

server_thread.start()
time.sleep(0.1)
client_thread.start()

server_thread.join()
client_thread.join()
