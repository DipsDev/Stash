import os
import pickle
import zlib

from models import Commit
from objects import write_file, read_file, hash_object, create_tree


class Actions:
    def __init__(self, repo: str):
        self.repo = repo
        self.full_repo = os.path.join(self.repo, ".stash")

    def cat_file(self, hash_id):
        """Cats the content of a file by its hash"""
        with open(os.path.join(self.full_repo, "objects", hash_id[:2], hash_id[2:]), "rb") as f:
            print(zlib.decompress(f.read()).decode())

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
        print('initialized empty repository at {}'.format(self.repo))

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
        print("added {} to the stash repo: {}".format(os.path.basename(path), sha1))

    def commit(self, message: str):
        """commits the changes and saves them"""
        # create the path to the indexes file, and read it
        index_path = os.path.join(self.full_repo, "index", "d")
        indices = pickle.loads(read_file(index_path))

        # create the tree
        sha1, tree = create_tree(self.repo, indices)

        # read the parent file
        parent = read_file(os.path.join(self.full_repo, "refs/head", "main"), binary_=False)
        # save the new tree to the current commit
        write_file(os.path.join(self.full_repo, "refs/head", "main"), sha1, binary_=False)

        # create the commit object and update it to the disk
        cmt = Commit(message, sha1, parent)
        commits = pickle.loads(read_file(os.path.join(self.full_repo, "refs/commit", "main")))
        commits[sha1] = cmt
        write_file(os.path.join(self.full_repo, "refs/commit", "main"), pickle.dumps(commits))

        print("commit added ", sha1)

    def push(self):
        """push changes to the cloud"""
        pass
