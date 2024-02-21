class TreeNode:
    def __init__(self, path: str, hash: str, type_="node"):
        self.path = path
        self.hash = hash
        self.type = type_

    def get_hash(self):
        return self.hash

    def get_path(self):
        return self.path

    def get_type(self):
        return self.type
