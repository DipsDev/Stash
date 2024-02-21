from models import TreeNode


class Tree(TreeNode):
    def __init__(self, path: str, hash: str, entries):
        super().__init__(path, hash, type_="tree")
        self.entries = entries
