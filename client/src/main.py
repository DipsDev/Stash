"""
Module that represents a main
"""

import handlers.cli_handler


def main():
    """

    :return:
    """
    handler = handlers.cli_handler.CLIHandler()
    handler.handle()


if __name__ == '__main__':
    main()
