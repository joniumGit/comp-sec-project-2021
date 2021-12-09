from scapy.layers.inet import IP

from ..interface import *


class ICMPServerFilter:

    def __call__(self, packet: IP) -> bool:
        try:
            if len(packet.options) == 0:
                return True
        except:
            return False


class ICMPClientFilter:

    def __call__(self, packet: IP) -> bool:
        try:
            if packet.options[0].option == 1:
                return True
        except:
            return False


class ICMPReverse(ProtocolReverseAdapter):

    def __init__(self, _filter):
        self._filter = _filter

    def __call__(self, message: bytes, wrapper: MessageContainer[MT]) -> MessageContainer[MT]:
        import base64
        from scapy.layers.inet import IP
        p = IP(message)
        if self._filter(p):
            try:
                wrapper << base64.decodebytes(p.lastlayer().load)
                return wrapper
            except Exception as e:
                pass
        return None

    def __invert__(self) -> 'ProtocolAdapter':
        return ICMPProtocol(self._filter)


class ICMPProtocol(ProtocolAdapter):

    def __init__(self, _filter):
        self._filter = _filter

    def __call__(self, message: MessageContainer[MT]) -> bytes:
        import base64
        from scapy.layers.inet import IP, ICMP
        return bytes(IP(dst=message.ip) / ICMP(type=0) / base64.encodebytes(~message))

    def __invert__(self) -> 'ProtocolReverseAdapter':
        return ICMPReverse(self._filter)


class ICMPServerProtocol(ICMPProtocol):

    def __call__(self, message: MessageContainer[MT]) -> bytes:
        import base64
        from scapy.layers.inet import IP, ICMP, IPOption_NOP
        return bytes(IP(dst=message.ip, options=[IPOption_NOP()]) / ICMP(type=0) / base64.encodebytes(~message))


class ICMPServer(AbstractServer):

    def __init__(self):
        super(ICMPServer, self).__init__(ICMPServerProtocol(ICMPServerFilter()))

    def handle_message(self, message: MessageContainer[MT]):
        if message.payload.message[-1] == 'd':
            message.payload.message += " 1"
        else:
            split = message.payload.message.rsplit(' ', maxsplit=1)
            message.payload.message = split[0] + f" {int(split[-1]) + 1}"
        self.send_message(message)


class ICMPClient(AbstractClient):

    def __init__(self):
        super(ICMPClient, self).__init__(ICMPProtocol(ICMPClientFilter()))

    def send_message(self, message: MessageContainer[MT]):
        if message.ip is None:
            message.ip = self.server_ip
        if message.port is None:
            message.port = 23
        super().send_message(message)

    def handle_message(self, message: MessageContainer[MT]):
        # time.sleep(1)
        self.log.info(str(message))
        self.send_message(message)


__all__ = ['ICMPServer', 'ICMPClient', 'BasicMessage']
