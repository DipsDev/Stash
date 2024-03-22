import sys


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
    def print_counter_numbers(cls, content: str, current=int, target=int):
        """
        Prints out a counter from the following format

        <user-content>: n / m

        """
        cls.replace_and_print(f"{content}: {current} / {target}")
