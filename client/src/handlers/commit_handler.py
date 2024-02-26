"""
Module that exposes the CommitHandler class, which handles all things related to commits
"""
import os
import pickle

import objects
from models.commit import Commit
from objects import write_file, read_file, create_tree


class CommitHandler:
    """Manages the handlers related to commits"""

    def __init__(self, repo, full_repo):
        self.full_repo = full_repo
        self.repo = repo

    def find_diff(self, commit1_sha, commit2_sha, branch="main"):
        """Finds the diff between two commits. given their hashes"""
        raise NotImplementedError()

    def get_head_commit(self, branch_name):
        """Returns the head commit hash by branch name"""
        return read_file(os.path.join(self.full_repo, "refs/head", branch_name), binary_=False)

    def extract_commit_data(self, sha1) -> Commit:
        """Returns the commit data by hash and branch name"""
        cmt = objects.resolve_object(self.full_repo, sha1).decode()
        lines = cmt.split("\n")
        del lines[2]

        assert lines[0][0:6] == "parent"
        parent_hash = lines[0][8::]

        assert lines[1][0:4] == "tree"
        tree_hash = lines[1][5::]

        message = lines[2]

        return Commit(message, tree_hash=tree_hash, parent=parent_hash)

    def commit(self, message: str, branch_name: str):
        """commits the changes and saves them"""

        # create the path to the indexes file, and read it
        index_path = os.path.join(self.full_repo, "index", "d")
        indices = pickle.loads(read_file(index_path))

        # create the tree
        tree_sha, _tree = create_tree(self.repo, indices, current_=self.repo)

        # read the parent file
        parent = read_file(os.path.join(self.full_repo, "refs/head",
                                        branch_name), binary_=False)

        cmt = Commit(message, tree_sha, parent)
        sha1 = objects.hash_object(self.repo, str(cmt).encode())

        # save the new tree to the current commit
        write_file(os.path.join(self.full_repo, "refs/head",
                                branch_name), sha1, binary_=False)

        return sha1
