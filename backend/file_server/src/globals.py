import zlib
from enum import Enum


class ResponseCode(Enum):
    ERROR = "stash-error"
    SEND_OBJECT = "stash-send-object"
    RECEIVE_OBJECT = "stash-receive-object"
    RECEIVE_HEAD_COMMIT = "stash-receive-head-commit"
    AUTHORIZED = "stash-authorized"


def parse_pkt(data: bytes, binary_data=False) -> (str, str):
    """Parses the pkt line format to command name, data"""
    if not binary_data:
        data = data.decode()
        header_length = int(data[:4])
        header = data[4:4 + header_length]
        return header, data[5 + header_length::]

    header_length = int(data[:4].decode())
    header = data[4:4 + header_length].decode()
    return header, zlib.decompress(data[5 + header_length::]).decode()


def create_pkt_line(command_name: ResponseCode, data: str | bytes):
    """Encodes the data to pkt line format"""
    command_name_length = str(len(str(command_name.value))).zfill(4)
    if type(data) == str:
        d = f"{command_name_length}{command_name.value}\n{data}"
        return d.encode()

    d = f"{command_name_length}{command_name.value}\n".encode() + data
    return d


