import struct
from typing import List, Tuple, Literal

PACKET_MAX = 65535

TIMESTAMP_SIZE = 4
CUSTOM_HEADER_SIZE = 4
OPTION_HEADER_SIZE = 4
BPO = Literal[
    4,
    8,
    12,
    16,
    20,
    24,
    28,
    32,  # Minus empty TS
    # 36  # Minus header
]

USE_EMPTY_TS = False


class Protocol:
    PREFIX: int = 0x1 << 7  # Custom timestamp flag (RFC 791)
    TRANSMISSION: int = 0x1 << 6  # Transmission 0 | Message 1
    TYPE_POSITION = 24
    ID_POSITION = 8


class Status:
    START: int = 0x1 << 4
    END: int = 0x1 << 5


class MessageType:
    """
    0 - 15
    """
    DATA: int = 1  # 0001
    ENCRYPTION: int = 2  # 0010
    EC_PUB_REQ: int = 4  # 0110
    EC_CON_REQ: int = 4  # 1010


class Utils:

    @staticmethod
    def to_option(header: bytes, data: bytes) -> bytes:
        length = struct.pack("!B", CUSTOM_HEADER_SIZE + len(data) + OPTION_HEADER_SIZE + 4 * USE_EMPTY_TS)
        pointer = struct.pack("!B", CUSTOM_HEADER_SIZE + len(data) + OPTION_HEADER_SIZE + 1 + 4 * USE_EMPTY_TS)
        # return b'\x44' + length + pointer + b'\x03' + header + data
        return b'\x44' + length + pointer + b'\x00' + header + data + (b'\x00' * 4) * USE_EMPTY_TS

    @staticmethod
    def to_data(option: bytes) -> Tuple[bytes, bytes]:
        header = option[OPTION_HEADER_SIZE:OPTION_HEADER_SIZE + CUSTOM_HEADER_SIZE]
        data_length = int.from_bytes(header[3:], byteorder='big', signed=False)
        data = option[OPTION_HEADER_SIZE + CUSTOM_HEADER_SIZE:OPTION_HEADER_SIZE + CUSTOM_HEADER_SIZE + data_length]
        return header, data

    @staticmethod
    def split(data: bytes, /, size: BPO) -> List[bytes]:
        rem = len(data) % size
        if rem != 0:
            data = data + (size - rem) * b'\x00'
        return [data[i:i + size] for i in range(0, len(data), size)]

    @staticmethod
    def set_start_end(data: List[bytes], /) -> List[bytes]:
        data[0] = data[0][:OPTION_HEADER_SIZE] + (
                (data[0][OPTION_HEADER_SIZE] | Status.START) ^ Protocol.TRANSMISSION
        ).to_bytes(1, byteorder='big', signed=False) + data[0][OPTION_HEADER_SIZE + 1:]
        data[-1] = data[-1][:OPTION_HEADER_SIZE] + (
                (data[-1][OPTION_HEADER_SIZE] | Status.END) ^ Protocol.TRANSMISSION
        ).to_bytes(1, byteorder='big', signed=False) + data[-1][OPTION_HEADER_SIZE + 1:]
        return data

    @staticmethod
    def decode(data: List[bytes]) -> bytes:
        return b''.join(Utils.to_data(e)[1] for e in data)

    @staticmethod
    def encode(data: bytes, /, _type: int, _id: int, size: BPO) -> List[bytes]:
        pre = (
                ((Protocol.PREFIX | Protocol.TRANSMISSION | _type) << 24) | (_id << 8) | (size & 0xff)
        ).to_bytes(4, byteorder='big', signed=False)
        return [Utils.to_option(pre, part) for part in Utils.split(data, size=size)]


class Shifter:
    """
    Message header packing:

        | 0000 | 0000 | 0000 0000 0000 0000 | 0000 0000 |
        | HEAD | TYPE |         ID          | DATA LEN  |
    """

    @staticmethod
    def is_start(option: bytes) -> bool:
        return option[OPTION_HEADER_SIZE] & Status.START != 0

    @staticmethod
    def is_end(data: bytes) -> bool:
        return data[OPTION_HEADER_SIZE] & Status.END != 0

    @staticmethod
    def get_id(option: bytes) -> int:
        return int.from_bytes(
            option[OPTION_HEADER_SIZE + 1:OPTION_HEADER_SIZE + 3],
            byteorder='big',
            signed=False
        )

    @staticmethod
    def get_type(option: bytes) -> int:
        return option[OPTION_HEADER_SIZE] & 0x0f

    @staticmethod
    def encode_message(
            data: bytes,
            sender_id: int,
            /,
            secret: bytes,
            bytes_per_option: BPO = 16,
    ) -> List[bytes]:
        import os
        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

        _id = sender_id & 0xffff

        nonce = os.urandom(12)
        nonce_data = Utils.encode(nonce, _type=MessageType.ENCRYPTION, _id=_id, size=min([12, bytes_per_option]))

        cip = ChaCha20Poly1305(secret)
        raw_bytes = cip.encrypt(nonce, data, _id.to_bytes(4, byteorder='big', signed=False))
        encoded_data = Utils.encode(raw_bytes, _type=MessageType.DATA, _id=_id, size=bytes_per_option)

        return Utils.set_start_end(nonce_data + encoded_data)

    @staticmethod
    def decode_message(data: List[bytes], /, secret: bytes) -> bytes:
        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
        from cryptography.exceptions import InvalidTag

        _id = Shifter.get_id(data[0])
        nonce = Utils.decode([part for part in data if Shifter.get_type(part) == MessageType.ENCRYPTION])
        data = Utils.decode([part for part in data if Shifter.get_type(part) == MessageType.DATA]).rstrip(b'\x00')

        cip = ChaCha20Poly1305(secret)
        try:
            return cip.decrypt(nonce, data, _id.to_bytes(4, byteorder='big', signed=False))
        except InvalidTag:
            raise ValueError("Failed to verify")
