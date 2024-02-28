"""
Main class
"""
import os
import pickle

from actions import Actions
from handlers import cli_parser
from objects import read_file, write_file


class Stash:
    """The main stash class"""

    def __init__(self, folder_path, print_mode_=False):
        self.folder_path = folder_path
        self.print_mode = print_mode_

        if not os.path.exists(self.folder_path):
            raise FileNotFoundError("stash: couldn't find repository folder.")

        self.repo_path = os.path.join(folder_path, ".stash")
        self.initialized = os.path.exists(self.repo_path)
        self.stash_actions = Actions(folder_path)

        self.current_branch_ref = "refs/head/main"
        self.branch_name = "main"
        if os.path.exists(os.path.join(self.repo_path, "HEAD")):
            unmod_ref = read_file(os.path.join(self.repo_path, "HEAD"), binary_=False)
            self.current_branch_ref = unmod_ref.split(" ")[1]  # ref: refs/head/main
            self.branch_name = self.current_branch_ref.split("/")[-1]

    @cli_parser.register_command(lambda params: len(params) == 0)
    def init(self):
        """Initialize the repository"""
        assert not self.initialized, "stash: repository is already initialized. See 'stash --help'."

        self.stash_actions.init()
        self.initialized = True
        self.current_branch_ref = "refs/head/main"
        if not self.print_mode:
            print(f'stash: initialized empty repository at {self.folder_path}.')

    @cli_parser.register_command(lambda params: len(params) >= 1)
    def commit(self, message: str):
        """Commit the changes to the current branch"""
        assert self.initialized, "stash: repository isn't initialized, use 'stash init'."

        cmt_hash = self.stash_actions.commit(message, self.branch_name)
        if self.print_mode:
            return cmt_hash

        print("stash: changes were committed")
        return cmt_hash

    @cli_parser.register_command(lambda params: len(params) == 0)
    def push(self):
        """Push the commits to the cloud"""
        assert self.initialized, "stash: repository isn't initialized, use 'stash init'."

        self.stash_actions.push("tcp:localhost:5000", self.branch_name)

    @cli_parser.register_command(lambda params: len(params) == 1)
    def add(self, filename: str):
        """Add a file to the index list"""
        assert self.initialized, "stash: repository isn't initialized, use 'stash init'."

        self.stash_actions.add(filename)

        if not self.print_mode:
            print(f"stash: added {filename} to local repository.")

    @cli_parser.register_command(lambda params: len(params) >= 1)
    def checkout(self, branch_name: str, upsert=False):
        """Switch to a different branch, or create a new one"""
        assert self.initialized, "stash: repository isn't initialized, use 'stash init'."

        branch_exists = os.path.exists(os.path.join(self.repo_path, "refs/head", branch_name))
        if not branch_exists and not upsert:
            print("stash: branch does not exist.")
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

        print(f"stash: switched branch, now in {branch_name}.")
