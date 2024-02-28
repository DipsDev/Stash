"""
Module that handles cli parsing
"""
import os
from handlers.cli_parser import CLIParser
import stash


class CLIHandler:
    """Handles IO CLI"""

    def __init__(self):
        self.__parser = CLIParser()
        self.__stash = stash.Stash(os.getcwd())

    @classmethod
    def get_available_commands(cls):
        """Returns a tuple of available commands"""
        return CLIParser.commands

    def handle(self):
        """Handles the entire control flow"""
        cmd, params = self.__parser.parse_args()
        av_cmds = self.get_available_commands()

        if cmd not in av_cmds:
            print(f"stash: '{cmd}' is not a stash command. See 'stash --help'.")
            return

        if cmd == "init":
            if not av_cmds.get(cmd)(params):
                print(f"stash: '{cmd}' supposed to receive 0 additional parameters,"
                      f" but got {len(params)}. See 'stash --help'.")
                return
            self.__stash.init()
            return

        if cmd == "commit":
            if not av_cmds.get(cmd)(params):
                print(f"stash: '{cmd}' supposed to receive 0 additional parameters,"
                      f" but got {len(params)}. See 'stash --help'.")
                return
            self.__stash.commit(" ".join(params))
            return
