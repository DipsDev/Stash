"""
Module that exports the tree class
"""
import objects
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
    def parse_tree(cls, tree_data: str) -> dict[str, TreeNode]:
        """Parse a tree"""
        parsing = {}
        splits = tree_data.split("\n")
        del splits[-1]
        prev = [d.split(" ") for d in splits]
        for i in prev:
            parsing[i[-1]] = TreeNode(path=i[-1], node_hash=i[1], type_=i[0])
        return parsing

    @classmethod
    def traverse_tree(cls, full_repo, tree_hash: str):
        """Traverses a tree and returns all of it's contents"""

        tree_data_encoded = objects.resolve_object(full_repo, tree_hash)
        tree = Tree.parse_tree(tree_data_encoded.decode())
        lines = ""
        for key, obj in tree.items():
            if obj.get_type() == "tree":
                lines += cls.traverse_tree(full_repo, obj.get_hash())
            else:
                lines += f"{obj.get_type()} {obj.get_hash()} {obj.get_path()}\n"

        return lines
