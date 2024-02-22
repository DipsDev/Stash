"""
Module that exports the tree node class
"""


class TreeNode:
    """
    Class representing a commit tree node.

    Attributes:
        path (str): The path of the node.
        node_hash (str): The hash of the node.
        type_ (str): The type of the node.
    """

    def __init__(self, path: str, node_hash: str, type_="node"):
        self.path = path
        self.hash = node_hash
        self.type = type_

    def get_hash(self):
        """get node hash"""
        return self.hash

    def get_path(self):
        """get node path"""
        return self.path

    def get_type(self):
        """get node type"""
        return self.type
