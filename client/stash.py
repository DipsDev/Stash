"""
Main class
"""
import os
import pickle

from actions import Actions
from objects import read_file, write_file


class Stash:
    """The main stash class"""

    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.repo_path = os.path.join(folder_path, ".stash")
        self.initialized = os.path.exists(self.repo_path)
        self.stash_actions = Actions(folder_path)

        self.current_branch_ref = None
        self.branch_name = None
        if os.path.exists(os.path.join(self.repo_path, "HEAD")):
            unmod_ref = read_file(os.path.join(self.repo_path, "HEAD"), binary_=False)
            self.current_branch_ref = unmod_ref.split(" ")[1]  # ref: refs/head/main
            self.branch_name = self.current_branch_ref.split("/")[-1]

    def init(self):
        """Initialize the repository"""
        self.stash_actions.init()
        self.initialized = True
        self.current_branch_ref = "refs/head/main"

    def commit(self, message: str):
        """Commit the changes to the current branch"""
        assert self.initialized, "Stash repository isn't initialized, use stash init to start"

        self.stash_actions.commit(message, self.branch_name)

    def push(self):
        """Push the commits to the cloud"""
        assert self.initialized, "Stash repository isn't initialized, use stash init to start"

        self.stash_actions.push("tcp:localhost:5000", self.branch_name)

    def add(self, filename: str):
        """Add a file to the index list"""
        assert self.initialized, "Stash repository isn't initialized, use stash init to start"

        self.stash_actions.add(os.path.join(self.folder_path, filename))

    def checkout(self, branch_name: str, upsert=False):
        """Switch to a different branch, or create a new one"""
        branch_exists = os.path.exists(os.path.join(self.repo_path, "refs/head", branch_name))
        if not branch_exists and not upsert:
            print("Branch does not exist")
            return

        # Create the branch if not exists
        if not branch_exists and upsert:
            write_file(os.path.join(self.repo_path, "refs", "commit", branch_name),
                       pickle.dumps({}))
            write_file(os.path.join(self.repo_path, "refs", "head", branch_name), "", binary_=False)

        write_file(os.path.join(self.repo_path, "HEAD"),
                   f"ref: refs/head/{branch_name}", binary_=False)
        self.branch_name = branch_name
        self.current_branch_ref = f"refs/head/{branch_name}"

        print(f"Switched branch, now in {branch_name}")
