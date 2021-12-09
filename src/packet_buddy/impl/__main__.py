from threading import Thread

from . import ICMPClient as ClientBase, ICMPServer as ServerBase, BasicMessage

TEST_MESSAGES = {
    'Hello World': 'Cool',
    'Cool': 'OK',
    'OK': 'GOT IT',
    'GOT IT': 'ME too',
    'ME too': 'Exit'
}


class IMPL:

    def handle_message(self, message):
        try:
            self.log.info(str(message))
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
        print("Server starting...")
        with ICMPServer[BasicMessage]() as server:
            self._kill = server._kill
            server.serve()
        print("Server exiting...")


class Client(Thread):

    def run(self) -> None:
        super().run()
        print("Client starting...")
        with ICMPClient[BasicMessage]() as client:
            self._kill = client._kill
            m = client.new_message()
            m << BasicMessage(message="Hello World", verifier="lol")
            client.send_message(m)
            client.serve()
        print("Client exiting...")


server_thread = Server(daemon=True)
client_thread = Client(daemon=True)

server_thread.start()
client_thread.start()

server_thread.join()
client_thread.join()
