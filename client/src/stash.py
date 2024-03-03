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

    @cli_parser.register_command(0)
    def init(self):
        """Create an empty Stash repository or reinitialize an existing one"""
        if self.initialized:
            print("stash: repository is initialized, use 'stash help'.")
            return

        self.stash_actions.init()
        self.initialized = True
        self.current_branch_ref = "refs/head/main"
        if not self.print_mode:
            print(f'stash: initialized empty repository at {self.folder_path}.')

    @cli_parser.register_command(1)
    def commit(self, message: str):
        """Record changes to the repository"""
        if not self.initialized:
            print("stash: repository isn't initialized, use 'stash init'.")
            return ""

        cmt_hash = self.stash_actions.commit(message, self.branch_name)
        if self.print_mode:
            return cmt_hash

        print("stash: changes were committed")
        return cmt_hash

    @cli_parser.register_command(0)
    def push(self):
        """Update remote refs along with associated objects"""
        if not self.initialized:
            print("stash: repository isn't initialized, use 'stash init'.")
            return

        self.stash_actions.push("tcp:localhost:5000", self.branch_name)

    @cli_parser.register_command(1)
    def add(self, filename: str):
        """Add file contents to the index"""
        if not self.initialized:
            print("stash: repository isn't initialized, use 'stash init'.")
            return

        self.stash_actions.add(filename)

        if not self.print_mode:
            print(f"stash: added {filename} to local repository.")

    @cli_parser.register_command(1)
    def checkout(self, branch_name: str, upsert=False):
        """Switch branches or restore working tree files

        Updates files in the working tree to match the version in the index or the specified tree.
        If no pathspec was given,
            git checkout will also update HEAD to set the specified branch as the current branch.

        """
        if not self.initialized:
            print("stash: repository isn't initialized, use 'stash init'.")
            return

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
