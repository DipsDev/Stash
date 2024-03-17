"""
Module that exports the Actions class
"""
import os
import pickle
import zlib

import objects
from handlers.commit_handler import CommitHandler
from handlers.remote_connection_handler import RemoteConnectionHandler
from models.commit import Commit
from objects import write_file, read_file, hash_object


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
        index_path = os.path.join(self.full_repo, "index", "d")
        # Load the database
        indices = pickle.loads(read_file(index_path))
        sha1 = hash_object(self.repo, read_file(path))
        # Update the database
        indices[path] = sha1

        write_file(index_path, pickle.dumps(indices))

    def commit(self, message: str, branch_name: str):
        """commits the changes and saves them locally"""

        return self.commit_handler.commit(message, branch_name)

    def push(self, branch_name: str):
        """push changes to the cloud"""

        current_commit = self.commit_handler.get_head_commit(branch_name)
        commit_data: Commit = self.commit_handler.extract_commit_data(current_commit)
        assert commit_data is not None

        # fetch the current commit from the web_server
        # find_diff between the current local version and remote version
        # send the diff files
        self.remote_connection_handler.connect()
        print('HELLO')
        print(self.commit_handler.find_diff(current_commit, "", remote_=True))
