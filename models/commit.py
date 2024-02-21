class Commit:
    def __init__(self, message: str, hash: str, parent: str):
        self.parent = parent
        self.hash = hash
        self.message = message

    def get_message(self):
        return self.message

    def get_hash(self):
        return self.hash

    def get_parent_hash(self):
        return self.parent