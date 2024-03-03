"""
Module that exports the commit class
"""


class Commit:
    """
    Class representing a commit.

    Attributes:
        message (str): The message of the commit.
        tree_hash (str): The hash of the commit.
        parent (str): The hash of the parent commit.
    """

    def __init__(self, message: str, tree_hash: str, parent: str):
        self.parent = parent
        self.hash = tree_hash
        self.message = message

    def get_message(self):
        """get commit's message"""
        return self.message

    def get_tree_hash(self):
        """get commit's hash"""
        return self.hash

    def get_parent_hash(self):
        """get commit's parent hash"""
        return self.parent

    def __str__(self):
        final_str = f"parent {self.parent}\ntree {self.hash}\n\n{self.message}"
        return final_str
