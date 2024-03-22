import sys
from enum import Enum


class ColorCode(Enum):
    CEND = '\33[0m'
    CBOLD = '\33[1m'
    CITALIC = '\33[3m'
    CURL = '\33[4m'
    CBLINK = '\33[5m'
    CBLINK2 = '\33[6m'
    CSELECTED = '\33[7m'

    CBLACK = '\33[30m'
    CRED = '\33[31m'
    CGREEN = '\33[32m'
    CYELLOW = '\33[33m'
    CBLUE = '\33[34m'
    CVIOLET = '\33[35m'
    CBEIGE = '\33[36m'
    CWHITE = '\33[37m'

    CBLACKBG = '\33[40m'
    CREDBG = '\33[41m'
    CGREENBG = '\33[42m'
    CYELLOWBG = '\33[43m'
    CBLUEBG = '\33[44m'
    CVIOLETBG = '\33[45m'
    CBEIGEBG = '\33[46m'
    CWHITEBG = '\33[47m'

    CGREY = '\33[90m'
    CRED2 = '\33[91m'
    CGREEN2 = '\33[92m'
    CYELLOW2 = '\33[93m'
    CBLUE2 = '\33[94m'
    CVIOLET2 = '\33[95m'
    CBEIGE2 = '\33[96m'
    CWHITE2 = '\33[97m'

    CGREYBG = '\33[100m'
    CREDBG2 = '\33[101m'
    CGREENBG2 = '\33[102m'
    CYELLOWBG2 = '\33[103m'
    CBLUEBG2 = '\33[104m'
    CVIOLETBG2 = '\33[105m'
    CBEIGEBG2 = '\33[106m'
    CWHITEBG2 = '\33[107m'


class Logger:
    """A singleton class that handles printing to the terminal"""

    @classmethod
    def replace_and_print(cls, content: str):
        """Removes the current line on the screen, and update it's content"""
        sys.stdout.write('\r' + content)
        sys.stdout.flush()

    @classmethod
    def println(cls, content: str):
        """Prints a new line"""
        sys.stdout.write(content + '\n')
        sys.stdout.flush()

    @classmethod
    def custom(cls, content: str, color: ColorCode):
        """Prints out a custom colored line"""
        sys.stdout.write(color.value + content + ColorCode.CEND.value + '\n')
        sys.stdout.flush()

    @classmethod
    def error(cls, content: str):
        """Prints out an error line"""
        sys.stdout.write(ColorCode.CRED.value + content + ColorCode.CEND.value + '\n')
        sys.stdout.flush()

    @classmethod
    def highlight(cls, content: str):
        """Prints out a highlighted line"""
        sys.stdout.write(ColorCode.CBLUE.value + content + ColorCode.CEND.value + '\n')
        sys.stdout.flush()

    @classmethod
    def print_counter_numbers(cls, content: str, current=int, target=int):
        """
        Prints out a counter from the following format

        <user-content>: n / m

        """
        cls.replace_and_print(f"{content}: {current} / {target}")
