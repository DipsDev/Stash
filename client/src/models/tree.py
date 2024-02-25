"""
Module that exports the tree class
"""
from .tree_node import TreeNode


class Tree(TreeNode):
    """
    Class representing a commit tree.

    Attributes:
        path (str): The path of the tree.
        tree_hash (str): The hash of the tree.
        entries (list): The data of the tree.
    """

    def __init__(self, path: str, tree_hash: str, entries: list):
        super().__init__(path, tree_hash, type_="tree")
        self.entries = entries
