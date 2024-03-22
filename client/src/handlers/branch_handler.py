import os


class BranchHandler:
    """A class that responsible for merging, and branch handling"""

    def __init__(self, repo: str):
        self.folder_path = repo
        self.stash_path = os.path.join(repo, ".stash")

    def create_branch(self, name: str):
        """Creates a branch"""
