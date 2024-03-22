import os
import re
import sys

from handlers.logger_handler import Logger
from objects import write_file


class BranchHandler:
    """A class that responsible for merging, and branch handling"""

    def __init__(self, repo: str):
        self.folder_path = repo
        self.stash_path = os.path.join(repo, ".stash")

    def create_branch(self, name: str, last_commit_sha: str):
        """Creates a branch"""
        if not re.compile(r'^[A-Za-z0-9_.-]+$').match(name):
            Logger.println("stash: branch names cannot contain special characters or spaces.")
            sys.exit(1)
        branch_exists = os.path.exists(os.path.join(self.stash_path, "refs/head", name))
        if branch_exists:
            Logger.println(f"stash: branch '{name}' already exists")
            sys.exit(1)

        # Create the branch if not exists
        write_file(os.path.join(self.stash_path, "refs", "head", name), last_commit_sha, binary_=False)

        Logger.println(f"stash: created branch '{name}'.")

    def get_all_branches(self):
        """Returns a list with all the available branches"""
        branches_dir = os.listdir(os.path.join(self.stash_path, "refs", "head"))
        return branches_dir
