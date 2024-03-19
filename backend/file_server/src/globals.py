from enum import Enum


class ResponseCode(Enum):
    ERROR = "stash-error"
    SEND_OBJECT = "stash-send-object"
    RECEIVE_OBJECT = "stash-receive-object"
    RECEIVE_HEAD_COMMIT = "stash-receive-head-commit"
    AUTHORIZED = "stash-authorized"


def parse_pkt(data: str) -> (str, str):
    """Parses the pkt line format to command name, data"""
    header_length = int(data[:4])
    header = data[4:4+header_length]
    return header, data[5+header_length::]


def create_pkt_line(command_name: ResponseCode, data: str | bytes, data_binary_=False):
    """Encodes the data to pkt line format"""
    command_name_length = str(len(str(command_name.value))).zfill(4)
    if not data_binary_:
        d = f"{command_name_length}{command_name.value}\n{data}"
        return d.encode()

    d = f"{command_name_length}{command_name.value}\n".encode() + data
    return d


