"""
Module that exposes the CommitHandler class, which handles all things related to commits
"""
import os
import pickle

import objects
from models.commit import Commit
from models.tree import Tree
from models.tree_node import TreeNode
from objects import write_file, read_file


class CommitHandler:
    """Manages the handlers related to commits"""

    def __init__(self, repo, full_repo):
        self.full_repo = full_repo
        self.repo = repo

    def find_diff(self, commit1_sha, commit2_sha):
        """Finds the diff between two commits. given their hashes"""
        cmt1_data = self.extract_commit_data(commit1_sha)
        cmt2_data = self.extract_commit_data(commit2_sha)

        return self._find_tree_diffs(cmt1_data.get_hash(), cmt2_data.get_hash())

    def _find_tree_diffs(self, h1: str, h2: str):
        """Returns the diff between trees"""
        if h1 == h2:  # Same object
            return ""
        lines = ""
        h1_data = objects.resolve_object(self.full_repo, h1).decode()
        h2_data = objects.resolve_object(self.full_repo, h2).decode()

        parsed_h1 = Tree.parse_tree(h1_data)
        parsed_h2 = Tree.parse_tree(h2_data)

        for key, obj in parsed_h2.items():
            if key not in parsed_h1:
                lines += f"+ {key}\n"
                continue

            if obj.get_hash() != parsed_h1.get(key).get_hash():
                if obj.get_type() == "blob":
                    lines += f"~ {key}\n"
                elif obj.get_type() == "tree":
                    self._find_tree_diffs(parsed_h1.get(key).get_hash(), obj.get_hash())
                continue

        for key, obj in parsed_h1.items():
            if key not in parsed_h2:
                if obj.get_type() == "blob":
                    lines += f"- {key}\n"
                if obj.get_type() == "tree":
                    lines += f"- {key}\n"

        return lines

    def get_head_commit(self, branch_name):
        """Returns the head commit hash by branch name"""
        return read_file(os.path.join(self.full_repo, "refs/head", branch_name), binary_=False)

    def create_tree(self, files: dict, current_):
        """Creates a new commit tree"""
        entries = []
        for it in os.scandir(current_):
            if it.name == ".stash":
                continue
            full_path = os.path.join(current_, it.name)
            if it.is_file():
                if full_path in files:
                    sha1 = objects.hash_object(self.repo, read_file(full_path))
                    leaf = TreeNode(full_path, sha1)
                    entries.append(leaf)
            else:
                if len(os.listdir(full_path)) == 0:
                    continue
                new_sha1, new_entries = self.create_tree(files, full_path)
                entries.append(Tree(full_path, new_sha1, new_entries))

        final_str = ""
        for i in entries:
            final_str += f"{i.get_type()} {i.get_hash()} {i.get_path()}\n"

        sha1 = objects.hash_object(self.repo, final_str.encode(), type_="tree")
        return sha1, entries

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
        tree_sha, _tree = self.create_tree(indices, current_=self.repo)

        # read the parent file
        parent = read_file(os.path.join(self.full_repo, "refs/head",
                                        branch_name), binary_=False)

        cmt = Commit(message, tree_sha, parent)
        sha1 = objects.hash_object(self.repo, str(cmt).encode(), type_="commit")

        # save the new tree to the current commit
        write_file(os.path.join(self.full_repo, "refs/head",
                                branch_name), sha1, binary_=False)

        return sha1