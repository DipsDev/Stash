"""
Module that exports the Actions class
"""
import os
import pickle
import zlib

from models.commit import Commit
from objects import write_file, read_file, hash_object, create_tree, resolve_object_location


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
        # Create the actions object
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

    def __init__(self, repo: str):
        self.repo = repo
        self.full_repo = os.path.join(self.repo, ".stash")

    def cat_file(self, hash_id):
        """Cats the content of a file by its hash"""

        with open(os.path.join(self.full_repo, "objects", hash_id[:2], hash_id[2:]), "rb") as f:
            print(zlib.decompress(f.read()).decode())

    def ls_tree(self, tree_hash):
        """Prints out the contents of a commit tree"""

        tree_path = resolve_object_location(self.full_repo, tree_hash)
        tree = zlib.decompress(read_file(tree_path)).decode()
        print(tree)

    def init(self):
        """
        creates and initializes a new stash repository
        :return:
        """
        # create the .stash directory
        os.mkdir(self.full_repo)
        # create the required folders for the database
        for name in ["objects", "index", "refs", "refs/head", "refs/commit"]:
            os.mkdir(os.path.join(self.full_repo, name))

        # create the required files
        # indices file, where file indexes are stored
        write_file(os.path.join(self.full_repo, "index", "d"), pickle.dumps({}))

        # commit file, where commits are stored
        write_file(os.path.join(self.full_repo, "refs/commit", "main"), pickle.dumps({}))

        # head file, where current commit hash is stored
        write_file(os.path.join(self.full_repo, "refs/head", "main"), "", binary_=False)

        # Write the current branch to the HEAD file. default: main branch
        write_file(os.path.join(self.full_repo, "HEAD"), "ref: refs/head/main", binary_=False)

        print(f'initialized empty repository at {self.repo}')

    def add(self, path: str):
        """adds a new file for the index list - to be tracked"""

        path = os.path.join(self.repo, path)
        # Get the index database
        index_path = os.path.join(self.full_repo, "index", "d")
        # Load the database
        indices = pickle.loads(read_file(index_path))
        sha1 = hash_object(self.repo, read_file(path))
        # Update the database
        indices[os.path.basename(path)] = sha1

        write_file(index_path, pickle.dumps(indices))
        print(f"added {os.path.basename(path)} to the stash repo: {sha1}")

    def commit(self, message: str, branch_name: str):
        """commits the changes and saves them"""

        # create the path to the indexes file, and read it
        index_path = os.path.join(self.full_repo, "index", "d")
        indices = pickle.loads(read_file(index_path))

        # create the tree
        sha1, _tree = create_tree(self.repo, indices, current_=self.repo)

        # read the parent file
        parent = read_file(os.path.join(self.full_repo, "refs/head",
                                        branch_name), binary_=False)
        # save the new tree to the current commit
        write_file(os.path.join(self.full_repo, "refs/head",
                                branch_name), sha1, binary_=False)

        # create the commit object and update it to the disk
        cmt = Commit(message, sha1, parent)
        commits = pickle.loads(read_file(os.path.join(self.full_repo, "refs/commit",
                                                      branch_name)))
        commits[sha1] = cmt
        write_file(os.path.join(self.full_repo, "refs/commit", branch_name),
                   pickle.dumps(commits))

        print("commit added ", sha1)

    def push(self, connection_url: str, branch_name: str):
        """push changes to the cloud"""

        head_commit_path = os.path.join(self.full_repo, "refs/head", branch_name)
        current_commit = read_file(head_commit_path, binary_=False)
        loaded_commits = pickle.loads(read_file(
            os.path.join(self.full_repo, "refs/commit", branch_name)))
        commit_data: Commit = loaded_commits.get(current_commit)
        assert commit_data is not None

        tree_path = resolve_object_location(self.full_repo, commit_data.get_hash())
        _tree = zlib.decompress(read_file(tree_path)).decode()
        print("pushing commit ->", commit_data.get_message())
        print(f"to {connection_url}")
