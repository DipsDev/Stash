"""
Exposes the CLIParser class
"""
import sys


def register_command(check):
    """Register a command automatically"""

    def decorator(func):
        CLIParser.commands[func.__name__] = check

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


class CLIParser:
    """Class handles cli parser"""

    commands = {}

    def __init__(self):
        pass

    def parse_args(self):
        """Parses the arguments and returns"""
        del sys.argv[0]
        cmd = sys.argv[0]
        params = sys.argv[1::]
        return cmd, params
