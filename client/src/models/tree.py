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

    @classmethod
    def parse_tree(cls, tree_data) -> dict[str, TreeNode]:
        """Parse a tree"""
        parsing = {}
        splits = tree_data.split("\n")
        del splits[-1]
        prev = [d.split(" ") for d in splits]
        for i in prev:
            parsing[i[-1]] = TreeNode(path=i[-1], node_hash=i[1], type_=i[0])
        return parsing
