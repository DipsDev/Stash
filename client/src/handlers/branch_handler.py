import os
import re
import sys

import objects
from handlers.commit_handler import CommitHandler
from handlers.logger_handler import Logger
from models.tree import Tree
from objects import write_file


class BranchHandler:
    """A class that responsible for merging, and branch handling"""

    def __init__(self, repo: str, commit_handler: CommitHandler):
        self.folder_path = repo
        self.stash_path = os.path.join(repo, ".stash")
        self.commit_handler = commit_handler

    def delete_branch(self, branch_name: str):
        """Deletes a given branch"""
        branch_head_path = os.path.join(self.stash_path, "refs/head", branch_name)
        branch_exists = os.path.exists(branch_head_path)
        if branch_exists:
            os.remove(branch_head_path)

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

    def load_branch(self, branch_name: str):
        """Loads up a branch. Assuming branch_name is a valid branch."""
        current_cmt = self.commit_handler.get_head_commit(branch_name)
        commit_data = self.commit_handler.extract_commit_data(current_cmt)

        def apply_commit_tree(tree_hash: str):
            """Applies a commit tree to the cwd"""
            tree_object = objects.resolve_object(self.stash_path, tree_hash).decode()
            parsed_tree = Tree.parse_tree(tree_object)
            for key, obj in parsed_tree.items():
                if obj.get_type() == "tree":
                    apply_commit_tree(obj.get_hash())
                else:
                    pth = os.path.join(self.folder_path, key)
                    data = objects.resolve_object(self.stash_path, obj.get_hash())
                    write_file(pth, data=data, binary_=True)

        apply_commit_tree(commit_data.get_tree_hash())
