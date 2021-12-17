import struct
from enum import IntEnum
from typing import List, Tuple, Literal

PACKET_MAX = 65535

TIMESTAMP_SIZE = 4
CUSTOM_HEADER_SIZE = 4
OPTION_HEADER_SIZE = 4
BPO = Literal[4, 8, 16, 20, 24, 28, 32, 36]

SECRET = b'super duper secret key! Encrypt!'

PREFIX: int = 0x1 << 31  # Custom timestamp flag (RFC 791)
TRANSMISSION: int = 0x1 << 30  # Transmission 0 | Message 1


class Status:
    START: int = 0x1 << 29
    END: int = 0x1 << 28


class MessageType(IntEnum):
    """
    0 - 15
    """
    MASK: int = 15

    DATA: int = 1
    ENCRYPTION: int = 2
    ID: int = 4


class Utils:

    @staticmethod
    def to_option(header: bytes, data: bytes) -> bytes:
        length = struct.pack("!B", CUSTOM_HEADER_SIZE + len(data) + OPTION_HEADER_SIZE)
        pointer = struct.pack("!B", CUSTOM_HEADER_SIZE + len(data) + OPTION_HEADER_SIZE + 1)
        return b'\x44' + length + pointer + b'\x03' + header + data

    @staticmethod
    def to_data(option: bytes) -> Tuple[bytes, bytes]:
        header = option[OPTION_HEADER_SIZE:OPTION_HEADER_SIZE + CUSTOM_HEADER_SIZE]
        data_length = int.from_bytes(header[3:], byteorder='big', signed=False)
        data = option[OPTION_HEADER_SIZE + CUSTOM_HEADER_SIZE:data_length]
        return header, data

    @staticmethod
    def split(data: bytes, /, size: BPO) -> List[bytes]:
        rem = len(data) % size
        if rem != 0:
            data = data + (size - rem) * b'\x00'
        return [data[i:i + size] for i in range(0, len(data), size)]

    @staticmethod
    def set_start_end(data: List[bytes], /) -> List[bytes]:
        data_length = len(data)
        if data_length == 1:
            data[0] = data[0][:OPTION_HEADER_SIZE] + (
                    data[0][OPTION_HEADER_SIZE] | Status.END ^ TRANSMISSION
            ).to_bytes(1, byteorder='big', signed=False) + data[0][OPTION_HEADER_SIZE + 1:]
        else:
            data[0] = data[0][:OPTION_HEADER_SIZE] + (
                    data[0][OPTION_HEADER_SIZE] | Status.START ^ TRANSMISSION
            ).to_bytes(1, byteorder='big', signed=False) + data[0][OPTION_HEADER_SIZE + 1:]
            data[-1] = data[-1][:OPTION_HEADER_SIZE] + (
                    data[-1][OPTION_HEADER_SIZE] | Status.END ^ TRANSMISSION
            ).to_bytes(1, byteorder='big', signed=False) + data[-1][OPTION_HEADER_SIZE + 1:]
        return data

    @staticmethod
    def decode(data: List[bytes]) -> bytes:
        return b''.join(Utils.to_data(e)[1] for e in data)

    @staticmethod
    def encode(data: bytes, /, type_and_id: int, size: BPO) -> List[bytes]:
        pre = (PREFIX | TRANSMISSION | type_and_id | size).to_bytes(4, byteorder='big', signed=False)
        return [Utils.to_option(pre, part) for part in Utils.split(data, size=size)]


class Shifter:
    """
    Message header packing:

        | 0000 | 0000 | 0000 0000 0000 0000 | 0000 0000 |
        | HEAD | TYPE |         ID          | DATA LEN  |
    """

    TYPE_POSITION = 24
    ID_POSITION = 8

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
    def encode_message(data: bytes, sender_id: int, /, bytes_per_option: BPO = 4) -> List[bytes]:
        import os
        from cryptography.hazmat.primitives.ciphers import Cipher
        from cryptography.hazmat.primitives.ciphers.algorithms import ChaCha20

        _id = sender_id << Shifter.ID_POSITION

        nonce = os.urandom(16)
        nonce_data = Utils.encode(nonce, type_and_id=MessageType.ENCRYPTION | _id, size=bytes_per_option)

        cip = Cipher(ChaCha20(SECRET, nonce), mode=None).encryptor()
        raw_bytes = cip.update(data)
        encoded_data = Utils.encode(raw_bytes, type_and_id=MessageType.DATA | _id, size=bytes_per_option)

        return Utils.set_start_end(nonce_data + encoded_data)

    @staticmethod
    def decode_message(data: List[bytes]) -> bytes:
        from cryptography.hazmat.primitives.ciphers import Cipher
        from cryptography.hazmat.primitives.ciphers.algorithms import ChaCha20

        nonce = Utils.decode([part for part in data if Shifter.get_type(part) == MessageType.ENCRYPTION])
        data = Utils.decode([part for part in data if Shifter.get_type(part) == MessageType.DATA]).rstrip(b'\x00')

        cip = Cipher(ChaCha20(SECRET, nonce), mode=None).decryptor()
        return cip.update(data)


class Utils2:

    @staticmethod
    def split(data: bytes, /, size: int) -> List[bytes]:
        rem = len(data) % size
        if rem != 0:
            data = data + (size - rem) * b'\x00'
        return [data[i:i + size] for i in range(0, len(data), size)]

    @staticmethod
    def set_start_end(data: List[int], /) -> List[int]:
        data_length = len(data)
        if data_length == 1:
            data[0] = data[0] | Status.END ^ TRANSMISSION
        else:
            data[0] = data[0] | Status.START ^ TRANSMISSION
            data[-1] = data[-1] | Status.END ^ TRANSMISSION
        return data

    @staticmethod
    def to_bytes(_int: int, /, size: int = 2) -> bytes:
        return bytes([0xff & (_int >> (i * 8)) for i in range(0, 2)])

    @staticmethod
    def join(data: List[int], /, size: int = 2) -> bytes:
        return b''.join(Utils2.to_bytes(part, size) for part in data)

    @staticmethod
    def encode(data: bytes, /, prefix: int, size: int = 2) -> List[int]:
        out = list()
        split = Utils2.split(data, size=size)
        pre = PREFIX | TRANSMISSION | prefix
        for part in split:
            v = pre
            for i in range(0, size, 1):
                v |= part[i] << (i * 8)
            out.append(v)
        return out


class Shifter2:
    """
    Message packing into 32 bits:

    | 0000 | 0000 0000 | 0000 | 0000 0000 | 0000 0000 |
    | HEAD |    ID     | TYPE |         DATA          |

    HEAD:
        1      Custom timestamp (RFC 791
        1,0    Message, Data Transmission
        1,0    START (boolean)
        1,0    END   (boolean)

    ID:
        One byte transmission id

    TYPE:
        4 bits for message type (Allows for 16 kinds)

    DATA:
        Two bytes of data
    """
    ID_POSITION = 20
    TYPE_POSITION = 16

    @staticmethod
    def is_start(data: int) -> bool:
        return data & Status.START != 0

    @staticmethod
    def get_sender(data: int) -> int:
        return Utils2.to_bytes(data)[0] ^ Shifter2.get_tid(data)

    @staticmethod
    def is_end(data: int) -> bool:
        return data & Status.END != 0

    @staticmethod
    def get_tid(data: int) -> int:
        return (data >> Shifter2.ID_POSITION) & 0xff

    @staticmethod
    def encode_message(data: bytes, sender_id: int, /) -> List[int]:
        import os
        from cryptography.hazmat.primitives.ciphers import Cipher
        from cryptography.hazmat.primitives.ciphers.algorithms import ChaCha20

        _tid = os.urandom(1)
        tid = (_tid[0] ^ sender_id) << Shifter2.ID_POSITION
        transaction_data = Utils2.encode(_tid, prefix=MessageType.ID | tid)

        nonce = os.urandom(16)
        nonce_data = Utils2.encode(nonce, prefix=MessageType.ENCRYPTION | tid)

        cip = Cipher(ChaCha20(SECRET, nonce), mode=None).encryptor()
        raw_bytes = cip.update(data)
        encoded_data = Utils2.encode(raw_bytes, prefix=MessageType.DATA | tid)

        return Utils2.set_start_end(transaction_data + nonce_data + encoded_data)

    @staticmethod
    def decode_message(data: List[int]) -> bytes:
        from cryptography.hazmat.primitives.ciphers import Cipher
        from cryptography.hazmat.primitives.ciphers.algorithms import ChaCha20

        nonce = Utils2.join([
            part
            for part in data
            if (part >> Shifter2.TYPE_POSITION) & MessageType.MASK == MessageType.ENCRYPTION
        ])
        data = Utils2.join([
            part
            for part in data
            if (part >> Shifter2.TYPE_POSITION) & MessageType.MASK == MessageType.DATA
        ]).rstrip(b'\x00')

        cip = Cipher(ChaCha20(SECRET, nonce), mode=None).decryptor()
        return cip.update(data)
