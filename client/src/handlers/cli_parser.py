"""
Exposes the CLIParser class
"""
import sys


def register_command(num_of_params):
    """Register a command automatically"""

    def decorator(func):
        CLIParser.commands[func.__name__] = num_of_params, func.__doc__

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


class CLIParser:
    """Class handles cli parser"""

    commands = {}

    def __init__(self):
        pass

    def generate_general_help_message(self):
        """generate a general help message, with description for each command"""
        fnl_string = "These are common Stash command:\n\n"
        for func_name, (_, docstring) in self.commands.items():
            fnl_string += f" {func_name}{' ' * (15 - len(func_name))}" +\
                          docstring.split("\n")[0] + "\n"

        fnl_string += "\nSee 'stash help <command>' to read about a specific subcommand."
        return fnl_string

    def print_help_message(self, command_name=None):
        """print the help message of a command"""
        if command_name is not None and command_name not in self.commands:
            print(f"stash: '{command_name}' is not a stash command. See 'stash help'.")
            return
        if command_name is None:
            print(self.generate_general_help_message())
            return

        print(f"Showing documentation for 'stash {command_name}'")
        print(self.commands.get(command_name)[1])

    def parse_args(self):
        """Parses the arguments and returns"""
        del sys.argv[0]
        cmd = sys.argv[0]

        flags = {}
        params = []

        # parse the flags
        for _, val in enumerate(sys.argv[1::]):
            if val.startswith("--"):
                flags[val[2::]] = True
            else:
                params.append(val)

        return cmd, params, flags
