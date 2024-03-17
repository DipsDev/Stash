from enum import Enum


class ResponseCode(Enum):
    ERROR = "stash-error"
    SEND_OBJECT = "stash-send-object"
    RECEIVE_OBJECT = "stash-receive-object"
    RECEIVE_HEAD_COMMIT = "stash-receive-head-commit"
    AUTHORIZED = "stash-authorized"


def parse_pkt(data: str) -> (str, str):
    """Parses the pkt line format to command name, data"""
    d = data.split("\n")
    return d[0], d[1]


def create_pkt_line(command_name: ResponseCode, data: str | bytes, data_binary_=False):
    """Encodes the data to pkt line format"""
    if not data_binary_:
        d = f"{command_name.value}\n{data}\n0000"
        return d.encode()

    d = f"{command_name.value}\n".encode() + data + "\n0000".encode()
    return d


