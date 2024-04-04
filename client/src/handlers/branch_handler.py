import os
import re
import shutil
import sys

import objects
from handlers.commit_handler import CommitHandler
from handlers.logger_handler import Logger
from handlers.remote_connection_handler import RemoteConnectionHandler
from models.tree import Tree
from objects import write_file


class BranchHandler:
    """A class that responsible for merging, and branch handling"""

    def __init__(self, repo: str, commit_handler: CommitHandler, remote_handler: RemoteConnectionHandler):
        self.folder_path = repo
        self.stash_path = os.path.join(repo, ".stash")
        self.commit_handler = commit_handler
        self.remote_handler = remote_handler

    def delete_branch(self, branch_name: str):
        """Deletes a given branch"""
        branch_head_path = os.path.join(self.stash_path, "refs/head", branch_name)
        branch_exists = os.path.exists(branch_head_path)
        if branch_exists:
            os.remove(branch_head_path)

    def can_fast_forward(self, from_branch_name: str, to_branch_name: str):
        """Check if commit2 is an ancestor of target."""
        #             from
        # C0 <- C1 <- C2 <- C3
        #                   to

        target = self.commit_handler.get_head_commit(from_branch_name)

        commit2 = self.commit_handler.get_head_commit(to_branch_name)
        tree_hash = self.commit_handler.extract_commit_data(commit2)
        pointer = tree_hash.get_parent_hash()

        while pointer != "":
            if pointer == target:
                return True

            pointer = self.commit_handler.extract_commit_data(pointer).get_parent_hash()

        return False

    def local_fast_forward_merge(self, local_branch_name: str, local_branch_name2: str):
        """Fast-Forward merge between 2 local branches. local_branch_name -> local_branch_name2. Assumes they can be
        fast-forwarded merge """

        to_commit = self.commit_handler.get_head_commit(local_branch_name2)
        write_file(os.path.join(self.stash_path, "refs", "head", local_branch_name), to_commit, binary_=False)
        self.load_branch(local_branch_name)

    def local_three_way_merge(self, current_branch_name: str, to_branch_name: str):
        """
        Three-way-merge between 2 local branches, which are diverge from an original commit.
        Assumes the branches have different commit.

                        main
                <- b1 <- b2
        c1 <- c2
                <- a1 <- a2
                        hotfix
        """

        current_latest_head = self.commit_handler.get_head_commit(current_branch_name)
        head_2 = self.commit_handler.get_head_commit(to_branch_name)

        if current_latest_head == head_2:
            Logger.error("stash: can't merge branches. they are the same.")
            exit(1)

        # Find the intersection point of the two branches
        pnt1 = current_latest_head
        pnt2 = head_2

        mutual_commit_hash = None

        while pnt1 != pnt2:
            if pnt1 == "":
                pnt1 = head_2

            if pnt2 == "":
                pnt2 = current_latest_head

            pnt1 = self.commit_handler.extract_commit_data(pnt1).get_parent_hash()
            pnt2 = self.commit_handler.extract_commit_data(pnt2).get_parent_hash()

            if pnt1 == pnt2:
                mutual_commit_hash = pnt2
                break

        if mutual_commit_hash == "":
            Logger.error("stash: couldn't merge branches. No mutual commit was found.")
            exit(1)

        # Find what's changed between both branches to the mutual commit hash,
        # If there are changes at the same file, throw an error saying there's a conflict.
        # We will deal with conflicts later.

        latest_current_changes = self.commit_handler.find_diff(mutual_commit_hash, current_latest_head)
        other_changes = self.commit_handler.find_diff(mutual_commit_hash, head_2).split("\n")
        del other_changes[-1]

        apply_changes = latest_current_changes.split("\n")
        del apply_changes[-1]
        apply_changes_set = set(apply_changes)

        changes = []

        # Check for changes, if there are changes for the same file. throw an error of conflict.
        for x in other_changes:
            tp, hsh, pth = x.split(" ")
            changes.append((tp, hsh, pth))
            if pth in apply_changes_set and tp == "blob":
                raise NotImplementedError(f"Conflicts are not handled yet. conflict in {pth}.")

        # Upload other_changes files
        # Commit all files
        # Reload branch

        for change in changes:
            file_type, file_hash, file_path = change
            abs_path = os.path.join(self.folder_path, file_path)
            if file_type == "tree" and not os.path.exists(abs_path):
                os.mkdir(abs_path)
            if file_type == "blob":
                write_file(abs_path, objects.resolve_object(self.stash_path, file_hash), binary_=True)

        self.commit_handler.commit(f"Merge {to_branch_name} -> {current_branch_name}", current_branch_name)
        self.load_branch(current_branch_name)

    def create_branch(self, name: str, last_commit_sha: str):
        """Creates a branch"""
        if not re.compile(r'^[A-Za-z0-9_.-]+$').match(name):
            Logger.println("stash: branch names cannot contain special characters or spaces.")
            exit(1)
        branch_exists = os.path.exists(os.path.join(self.stash_path, "refs/head", name))
        if branch_exists:
            Logger.println(f"stash: branch '{name}' already exists")
            exit(1)

        # Create the branch if not exists
        write_file(os.path.join(self.stash_path, "refs", "head", name), last_commit_sha, binary_=False)

    def get_all_branches(self):
        """Returns a list with all the available branches"""
        branches_dir = os.listdir(os.path.join(self.stash_path, "refs", "head"))
        return branches_dir

    def load_branch(self, branch_name: str):
        """Loads up a branch. Assuming branch_name is a valid branch."""
        current_cmt = self.commit_handler.get_head_commit(branch_name)
        commit_data = self.commit_handler.extract_commit_data(current_cmt)

        def apply_commit_tree(tree_hash: str, pth=self.folder_path, folder_path_length=len(self.folder_path) + 1):
            """Applies a commit tree to the cwd"""
            tree_object = objects.resolve_object(self.stash_path, tree_hash).decode()
            parsed_tree = Tree.parse_tree(tree_object)

            to_be_deleted = []
            for i in os.listdir(pth):
                # Note that 'i' is a filename, something like file.txt.
                real_path = os.path.join(pth, i)
                truncated_path = real_path[folder_path_length::]
                if i.startswith(".stash"):
                    continue
                if truncated_path not in parsed_tree:
                    to_be_deleted.append(i)

            for deleted_file in to_be_deleted:
                deleted_file_path = os.path.join(pth, deleted_file)
                if os.path.isdir(deleted_file_path):
                    shutil.rmtree(deleted_file_path)
                else:
                    os.remove(deleted_file_path)

            for key, obj in parsed_tree.items():
                # Note that key is a path, something like folder/file. then we need only the file
                file_location = os.path.join(self.folder_path, key)
                if obj.get_type() == "tree":
                    if not os.path.exists(file_location):
                        os.mkdir(file_location)
                    apply_commit_tree(obj.get_hash(), pth=file_location)
                else:
                    data = objects.resolve_object(self.stash_path, obj.get_hash())
                    write_file(file_location, data=data, binary_=True)

        apply_commit_tree(commit_data.get_tree_hash())
