"""
Module that handles cli parsing
"""
import os

from handlers.cli_parser import CLIParser
import stash
from handlers.logger_handler import Logger


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
        cmd, params, flags = self.__parser.parse_args()
        av_cmds = self.get_available_commands()

        if cmd == "help":
            self.__parser.print_help_message(params[0] if len(params) >= 1 else None)
            return

        if cmd not in av_cmds:
            Logger.println(f"stash: '{cmd}' is not a stash command. See 'stash help'.")
            return

        if av_cmds.get(cmd)[0] != len(params):
            Logger.println(f"stash: '{cmd}' is supposed to receive {av_cmds.get(cmd)[0]} additional parameters,"
                           f" but got {len(params)} instead. See 'stash help'.")
            return

        if cmd == "init":
            self.__stash.init()

        if cmd == "commit":
            self.__stash.commit(params[0])

        if cmd == "checkout":
            self.__stash.checkout(params[0], flags.get("b", False))

        if cmd == "add":
            self.__stash.add(params[0])

        if cmd == "push":
            self.__stash.push()

        if cmd == "branch":
            self.__stash.branch(params[0], flags)
