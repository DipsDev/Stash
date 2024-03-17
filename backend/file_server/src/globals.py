from enum import Enum


def parse_pkt(data: str) -> (str, str):
    """Parses the pkt line format to command name, data"""
    d = data.split("\n")
    return d[0], d[1]


def create_pkt_line(command_name: str, data: str):
    """Encodes the data to pkt line format"""
    d = f"{command_name}\n{data}\n0000"
    return d.encode()


class ResponseCode(Enum):
    ERROR = "stash-error"
