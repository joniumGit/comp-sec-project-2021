from typing import List

from scapy.layers.inet import IP

from ..interface import *


class ICMPServerFilter(ProtocolFilter):

    def __call__(self, data: bytes) -> bool:
        try:
            if len(IP(data).options) == 0:
                return True
        except:
            return False


class ICMPClientFilter(ProtocolFilter):

    def __call__(self, data: bytes) -> bool:
        try:
            if IP(data).options[0].option == 1:
                return True
        except:
            return False


class ICMPReverse(ProtocolReverseAdapter):

    def __call__(self, message: List[bytes], wrapper: MessageContainer[MT]) -> MessageContainer[MT]:
        import base64
        from scapy.layers.inet import IP
        p = IP(message[0])
        wrapper << base64.decodebytes(p.lastlayer().load)
        return wrapper

    def __invert__(self) -> 'ProtocolAdapter':
        return ICMPProtocol()


class ICMPProtocol(ProtocolAdapter):

    def __call__(self, message: MessageContainer[MT]) -> List[bytes]:
        import base64
        from scapy.layers.inet import IP, ICMP
        return [bytes(IP(dst=message.ip) / ICMP(type=0) / base64.encodebytes(~message))]

    def __invert__(self) -> 'ProtocolReverseAdapter':
        return ICMPReverse()


class ICMPServerProtocol(ICMPProtocol):

    def __call__(self, message: MessageContainer[MT]) -> List[bytes]:
        import base64
        from scapy.layers.inet import IP, ICMP, IPOption_NOP
        return [bytes(IP(dst=message.ip, options=[IPOption_NOP()]) / ICMP(type=0) / base64.encodebytes(~message))]

    def __invert__(self) -> 'ProtocolReverseAdapter':
        return ICMPReverse()


def make_socket():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
    return s


class ICMPServer(AbstractServer):

    def __init__(self):
        super(ICMPServer, self).__init__(ICMPServerProtocol(), ICMPServerFilter())

    def new_socket(self):
        return make_socket()

    def handle_message(self, message: MessageContainer[MT]):
        if message.payload.message[-1] == 'd':
            message.payload.message += " 1"
        else:
            split = message.payload.message.rsplit(' ', maxsplit=1)
            message.payload.message = split[0] + f" {int(split[-1]) + 1}"
        self.send_message(message)


class ICMPClient(AbstractClient):

    def __init__(self):
        super(ICMPClient, self).__init__(ICMPProtocol(), ICMPClientFilter())

    def new_socket(self):
        return make_socket()

    def send_message(self, message: MessageContainer[MT]):
        if message.ip is None:
            message.ip = self.server_ip
        if message.port is None:
            message.port = 23

        import hmac, base64

        if hasattr(message, 'payload'):
            if hasattr(message.payload, 'verifier'):
                message.payload.verifier = ""
                try:
                    h = hmac.HMAC(b"test", message.payload.json().encode('utf-8'), 'sha512')
                    message.payload.verifier = base64.encodebytes(h.digest())
                except Exception as e:
                    self.log.exception("", exc_info=e)

        super().send_message(message)

    def handle_message(self, message: MessageContainer[MT]):
        # time.sleep(1)
        self.log.info(f"Received: {message}")
        self.send_message(message)


__all__ = ['ICMPServer', 'ICMPClient', 'BasicMessage']
