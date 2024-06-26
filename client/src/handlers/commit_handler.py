"""
Module that exposes the CommitHandler class, which handles all things related to commits
"""
import os
import pickle
import sys

import objects
from handlers.logger_handler import Logger
from handlers.remote_connection_handler import RemoteConnectionHandler
from models.commit import Commit
from models.tree import Tree
from models.tree_node import TreeNode
from objects import write_file, read_file


class CommitHandler:
    """Manages the handlers related to commits"""

    def __init__(self, repo, full_repo, remote_handler: RemoteConnectionHandler):
        self.full_repo = full_repo
        self.repo = repo
        self.remote_handler = remote_handler

    def generate_prep_file(self, tree_hash: str):
        """
        Returns a preparefile for the given commit.
        prepfile contains all directories, subdirectories and files that the commit contains.
        """
        tree_data_encoded = objects.resolve_object(self.full_repo, tree_hash)
        tree = Tree.parse_tree(tree_data_encoded.decode())
        file = f"{tree_hash} tree\n"
        for key, obj in tree.items():
            if obj.get_type() == "tree":
                file += self.generate_prep_file(obj.get_hash())
            else:
                file += f"{obj.get_hash()} {obj.get_type()}\n"
        return file

    def find_diff(self, commit1_sha: str, commit2_sha: str, remote_=False, remote_branch="main", local_branch="main"):
        """Finds the diff between two commits. given their hashes"""
        if not remote_:
            cmt1_data = self.extract_commit_data(commit1_sha)
            cmt2_data = self.extract_commit_data(commit2_sha)

            return self._local_find_tree_diffs(cmt1_data.get_tree_hash(), cmt2_data.get_tree_hash())

        local_data = self.extract_commit_data(commit1_sha)
        remote_head_commit = self.remote_handler.get_remote_head_commit(remote_branch)
        if remote_head_commit == "":
            Logger.println("stash: Remote repository is empty. Fetching resources...")
            current_commit = self.extract_commit_data(self.get_head_commit(local_branch))
            d = self.generate_prep_file(current_commit.get_tree_hash()) + f"{commit1_sha} commit\n"
            return d

        remote_data = self.remote_handler.resolve_remote_commit_data(remote_head_commit)

        if remote_data.get_tree_hash() == local_data.get_tree_hash():
            Logger.println("stash: No changes were found.")
            exit(1)

        def roll_back_commits(commit_hash: str):
            """Returns a list of all commits that aren't available on the server"""
            if commit_hash == remote_head_commit or commit_hash == "":
                return []
            cmt_data = self.extract_commit_data(commit_hash)
            return [f"{commit_hash} commit\n"] + roll_back_commits(cmt_data.get_parent_hash())

        return self._remote_find_tree_diffs(remote_data.get_tree_hash(), local_data.get_tree_hash())\
               + "".join(roll_back_commits(commit1_sha))

    def compare_remote_with_local(self, local_hash: str, remote_hash: str):
        """compares the remote data to the local repo, and returns the changes to download locally"""
        if local_hash == remote_hash:
            return ""

        lines = f"{remote_hash} tree\n"
        parsed_local_data = objects.resolve_object(self.full_repo, local_hash).decode()
        parsed_remote_data = self.remote_handler.resolve_remote_object(remote_hash)

        parsed_remote = Tree.parse_tree(parsed_remote_data)
        parsed_local = Tree.parse_tree(parsed_local_data)

        for key, obj in parsed_remote.items():
            if key not in parsed_local:
                lines += f"{obj.get_hash()} {obj.get_type()}\n"
                continue

            if obj.get_hash() != parsed_local.get(key).get_hash():
                if obj.get_type() == "blob":
                    lines += f"{obj.get_hash()} {obj.get_type()}\n"
                elif obj.get_type() == "tree":
                    lines += f"{obj.get_hash()} tree\n" + \
                             self.compare_remote_with_local(parsed_local.get(key).get_hash(), obj.get_hash())
                continue
        return lines

    def _remote_find_tree_diffs(self, remote_hash: str, local_hash: str):
        """
        Creates a prepfile based on remote-local diffs.
        h1: local tree hash
        h2: remote tree hash
        """
        if local_hash == remote_hash:
            return ""
        lines = f"{local_hash} tree\n"

        # Check if object exists local, to decrease traffic
        if os.path.exists(objects.resolve_object_location(self.full_repo, remote_hash)):
            remote_data = objects.resolve_object(self.full_repo, remote_hash).decode()
        else:
            remote_data = self.remote_handler.resolve_remote_object(remote_hash)
        local_data = objects.resolve_object(self.full_repo, local_hash).decode()

        parsed_remote = Tree.parse_tree(remote_data)
        parsed_local = Tree.parse_tree(local_data)

        for key, obj in parsed_local.items():
            if key not in parsed_remote:
                Logger.println(f"+ {key}\n")
                lines += f"{obj.get_hash()} {obj.get_type()}\n"
                continue

            if obj.get_hash() != parsed_remote.get(key).get_hash():
                if obj.get_type() == "blob":
                    Logger.println(f"~ {key}\n")
                    lines += f"{obj.get_hash()} {obj.get_type()}\n"
                elif obj.get_type() == "tree":
                    lines += f"{obj.get_hash()} tree\n" + \
                             self._remote_find_tree_diffs(parsed_remote.get(key).get_hash(), obj.get_hash())
                continue

        for key, obj in parsed_remote.items():
            if key not in parsed_local:
                Logger.println(f"- {key}\n")

        return lines

    def _local_find_tree_diffs(self, h1: str, h2: str):
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
                if obj.get_type() == "blob":
                    lines += f"{obj.get_type()} {obj.get_hash()} {obj.get_path()}\n"
                if obj.get_type() == "tree":
                    lines += f"{obj.get_type()} {obj.get_hash()} {obj.get_path()}\n" + \
                             Tree.traverse_tree(self.full_repo, obj.get_hash())
                continue

            if obj.get_hash() != parsed_h1.get(key).get_hash():
                if obj.get_type() == "blob":
                    lines += f"{obj.get_type()} {obj.get_hash()} {obj.get_path()}\n"
                elif obj.get_type() == "tree":
                    lines += f"{obj.get_type()} {obj.get_hash()} {obj.get_path()}\n" + \
                             self._local_find_tree_diffs(parsed_h1.get(key).get_hash(), obj.get_hash())
                continue

        # for key, obj in parsed_h1.items():
        # if key not in parsed_h2:
        # if obj.get_type() == "blob":
        # lines += f"-{key}\n"
        # if obj.get_type() == "tree":
        # lines += f"-{key}\n"

        return lines

    def get_head_commit(self, branch_name):
        """Returns the head commit hash by branch name"""
        pth = os.path.join(self.full_repo, "refs/head", branch_name)
        if not os.path.exists(pth):
            raise FileNotFoundError("Branch cannot be found")
        return read_file(pth, binary_=False)

    def create_tree(self, files: dict, path_length, current_):
        """Creates a new commit tree"""
        entries = []
        for it in os.scandir(current_):
            if it.name == ".stash":
                continue
            full_path = os.path.join(current_, it.name)
            if full_path not in files:
                continue
            if it.is_file():
                sha1 = objects.hash_object(self.repo, read_file(full_path))
                leaf = TreeNode(full_path[path_length + 1::], sha1)
                entries.append(leaf)
            else:
                if len(os.listdir(full_path)) == 0:
                    continue
                new_sha1, new_entries = self.create_tree(files, path_length, full_path)
                entries.append(Tree(full_path[path_length + 1::], new_sha1, new_entries))

        final_str = ""
        for i in entries:
            final_str += f"{i.get_type()} {i.get_hash()} {i.get_path()}\n"

        sha1 = objects.hash_object(self.repo, final_str.encode(), type_="tree")

        return sha1, entries

    def extract_commit_data(self, sha1) -> Commit:
        """
        Extracts the commit data, given its hash value
        :param sha1: commit hash value
        :return: the commit data as Commit
        """
        cmt = objects.resolve_object(self.full_repo, sha1).decode()
        lines = cmt.split("\n")
        del lines[2]

        assert lines[0][0:6] == "parent"
        parent_hash = lines[0][7::]

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
        tree_sha, _tree = self.create_tree(indices, len(self.repo), current_=self.repo)

        # read the parent file
        parent = self.get_head_commit(branch_name)

        cmt = Commit(message, tree_sha, parent)
        sha1 = objects.hash_object(self.repo, str(cmt).encode(), type_="commit")

        # save the new tree to the current commit
        write_file(os.path.join(self.full_repo, "refs/head",
                                branch_name), sha1, binary_=False)

        return sha1
