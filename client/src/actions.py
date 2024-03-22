"""
Module that exports the Actions class
"""
import os
import pickle
import sys
import zlib

import objects
from handlers.branch_handler import BranchHandler
from handlers.commit_handler import CommitHandler
from handlers.remote_connection_handler import RemoteConnectionHandler
from objects import write_file


def load_ignore_file(path: str):
    """Loads an ignore file, to a dictionary"""
    if not os.path.isdir(path):
        raise Exception("'path' must be a valid dictionary.")
    ignore_path = os.path.join(path, ".stashignore")
    d = {}
    if os.path.exists(ignore_path):
        with open(ignore_path, "r") as f:
            for line in f.read().splitlines():
                d[line] = True

    return d


class Actions:
    """
    Class representing the stash repository.

    Attributes:
        repo (str): The path of the repository

    Methods:
        __init__: Initializes a repo object (not the actual repo).
        init: Initializes a repo database.
        cat_file: Prints out the content of an object.
        ls_tree: Prints out the contents of a commit tree.
        add: Adds a file to the index list.
        commit: Commits the current changes to the database
        push: Pushes the changes to the cloud

    Example Usage:
        # Create the handlers object
        my_actions = Actions("./test_repo")

        # Add files for indexing
        my_actions.add("my_text.txt")
        my_actions.add("my_python_file.py")

        # Commit the changes
        my_actions.commit("First Commit")

        # Push changes
        my_actions.push()

        # Change branch
        my_actions.checkout("dev", upsert=True)



    """

    def __init__(self, repo: str, remote_connection_handler: RemoteConnectionHandler):
        self.repo = repo
        self.full_repo = os.path.join(self.repo, ".stash")

        self.commit_handler = CommitHandler(self.repo, self.full_repo, remote_connection_handler)
        self.branch_handler = BranchHandler(self.repo)
        self.remote_connection_handler = remote_connection_handler

    def cat_file(self, hash_id):
        """Cats the content of a file by its hash"""

        with open(os.path.join(self.full_repo, "objects", hash_id[:2], hash_id[2:]), "rb") as f:
            print(zlib.decompress(f.read()).decode())

    def ls_tree(self, tree_hash):
        """Prints out the contents of a commit tree"""

        tree = objects.resolve_object(self.full_repo, tree_hash).decode()
        print(tree)

    def init(self):
        """
        creates and initializes a new stash repository
        :return:
        """
        # create the .stash directory
        os.mkdir(self.full_repo)
        # create the required folders for the database
        for name in ["objects", "index", "refs", "refs/head"]:
            os.mkdir(os.path.join(self.full_repo, name))

        # create the required files
        # indices file, where file indexes are stored
        write_file(os.path.join(self.full_repo, "index", "d"), pickle.dumps({}))

        # head file, where current commit hash is stored
        write_file(os.path.join(self.full_repo, "refs/head", "main"), "", binary_=False)

        # Write the current branch to the HEAD file. default: main branch
        write_file(os.path.join(self.full_repo, "HEAD"), "ref: refs/head/main", binary_=False)

    def add(self, path: str):
        """adds a new file for the index list - to be tracked"""

        path = os.path.join(self.repo, path)
        path = os.path.normpath(path)
        # Get the index database
        if not os.path.exists(path):
            print("stash: No file was found. Please check your spelling.")
            sys.exit(1)

        index_path = os.path.join(self.full_repo, "index", "d")
        # Load the database
        indices = pickle.loads(objects.read_file(index_path))

        if os.path.isdir(path):
            def traverse_dirs(p, ignores=None):
                if ignores is None:
                    ignores = {}
                b = []
                ignores.update(load_ignore_file(p))
                for entry in os.scandir(p):
                    if ignores.get(entry.name) is not None:
                        continue
                    if entry.name.startswith(".stash"):
                        continue
                    if entry.is_dir():
                        b.extend(traverse_dirs(entry.path, ignores))
                    b.append(entry.path)
                return b

            buffer = traverse_dirs(path)
            for i in buffer:
                indices[i] = True

        else:
            indices[path] = True

        write_file(index_path, pickle.dumps(indices))

    def commit(self, message: str, branch_name: str):
        """commits the changes and saves them locally"""

        return self.commit_handler.commit(message, branch_name)

    def branch(self):
        """Deletes or creates a branch"""

    def push(self, branch_name: str):
        """push changes to the cloud"""

        current_commit = self.commit_handler.get_head_commit(branch_name)
        assert current_commit != ""

        # fetch the current commit from the web_server
        # find_diff between the current local version and remote version
        # send the diff files
        self.remote_connection_handler.connect()
        prep_file = self.commit_handler.find_diff(current_commit, "", True)
        pack_file = self.remote_connection_handler.generate_pack_file(prep_file)
        self.remote_connection_handler.push_pkt("stash-send-packfile", pack_file)
        d = self.remote_connection_handler.push_pkt("stash-update-head", self.commit_handler.get_head_commit("main"))
        print(d)
        self.remote_connection_handler.close()
