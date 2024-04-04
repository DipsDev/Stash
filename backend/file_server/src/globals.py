import zlib
from enum import Enum


class ResponseCode(Enum):
    ERROR = "stash-error"
    SEND_OBJECT = "stash-send-object"
    RECEIVE_OBJECT = "stash-receive-object"
    RECEIVE_HEAD_COMMIT = "stash-receive-head-commit"
    AUTHORIZED = "stash-authorized"
    SEND_PACKFILE = "stash-send-packfile"
    OK = "stash-ok"
    UPDATE_HEAD = "stash-update-head"
    SEND_STREAM = "stash-send-stream"
    RECEIVE_PACKFILE = "stash-receive-packfile"


def parse_pkt(data: bytes) -> (str, bytes):
    """Parses the pkt line format to command name, data"""
    is_compressed = bool(int(data[:1].decode()))
    header_length = int(data[1:5].decode())
    header = data[5:5 + header_length].decode()

    if not is_compressed or header == ResponseCode.SEND_STREAM.value:
        return header, bytes(data[6 + header_length::])

    return header, zlib.decompress(bytes(data[6 + header_length::]))


def create_pkt_line(command_name: ResponseCode, data: str | bytes):
    """Encodes the data to pkt line format"""
    command_name_length = str(len(str(command_name.value))).zfill(4)
    if type(data) == str:
        d = f"0{command_name_length}{command_name.value}\n{data}"
        return d.encode()

    d = f"1{command_name_length}{command_name.value}\n".encode() + data
    return d
