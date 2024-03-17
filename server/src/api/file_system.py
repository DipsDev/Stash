import os
import sys
import zlib


def write_file(path, data, binary_=True):
    """
    Writes a file to the database
    :param binary_: Write binary, or text
    :param path: the file path
    :param data: file data in files
    :return:
    """
    with open(path, "wb" if binary_ else "w") as f:
        f.write(data)


def read_file(path, binary_=True) -> bytes or str:
    """Reads a binary file"""
    with open(path, "rb" if binary_ else "r") as f:
        return f.read()


def resolve_object(main_folder, repo_id, sha1) -> bytes:
    """Returns the original content of an object"""
    path = resolve_object_location(main_folder, repo_id, sha1)
    return zlib.decompress(bytes(read_file(path, binary_=True)))


def resolve_object_location(full_repo, repo_id, obj_hash):
    """resolves an object hash to its path on the disk"""
    return os.path.join(full_repo, repo_id, "objects", obj_hash[:2], obj_hash[2:])


class FileSystem:

    def __init__(self, storage_path: str):
        self.main_folder = storage_path

    def get_server_object(self, repo_id: str, s: str, c: str):
        """Fetch a server object from a remote repository"""
        assert len(s) == 2
        assert len(c) == 38
        if not os.path.exists(os.path.join(self.main_folder, repo_id, "objects", s, c)):
            return None

        obj = resolve_object(self.main_folder, repo_id, f"{s}{c}")
        return obj

    def get_repo_branches(self, repo_id: str) -> list[str]:
        """Gets the branches available in a repository"""
        return os.listdir(os.path.join(self.main_folder, repo_id, "refs", "head"))

    def get_head_commit(self, repo_id: str, branch: str):
        """Gets the current head commit"""
        head_commit_path = os.path.join(self.main_folder, repo_id, "refs/head", branch)
        if not os.path.exists(head_commit_path):
            return None
        cmt = read_file(head_commit_path, binary_=False)
        return cmt

    def extract_commit_data(self, repo_id: str, sha1) -> tuple:
        """Extracts the commit data, given its hash value"""
        cmt = resolve_object(self.main_folder, repo_id, sha1).decode()
        lines = cmt.split("\n")
        del lines[2]

        assert lines[0][0:6] == "parent"
        parent_hash = lines[0][7::]

        assert lines[1][0:4] == "tree"
        tree_hash = lines[1][5::]

        message = lines[2]

        return message, tree_hash, parent_hash

    def get_current_commit_files(self, repo_id: str, branch_name="main") -> (str, list[()]):
        """Returns a list of the current commit file names"""
        last_commit = read_file(os.path.join(self.main_folder, repo_id, "refs/head", branch_name), binary_=False)
        if last_commit == "":
            return []

        message, tree_hash, parent = self.extract_commit_data(repo_id, last_commit)

        # Traverse tree hash
        tree_view = self.get_server_object(repo_id, tree_hash[:2], tree_hash[2:]).decode().split("\n")
        tree_view.pop()  # Remove blank line

        files_commit = []
        for row in tree_view:
            tp, hsh, filename = row.split(" ")
            files_commit.append((tp, hsh, filename))
        return message, files_commit

    def allocate_repository(self, repo_id: str):
        """Allocates a new repository in the filesystem"""
        os.mkdir(os.path.join(self.main_folder, repo_id))

        # create the required folders for the database
        for name in ["objects", "index", "refs", "refs/head"]:
            os.mkdir(os.path.join(self.main_folder, repo_id, name))

        # create the required files
        # indices file, where file indexes are stored
        # write_file(os.path.join(self.main_folder, repo_id, "index", "d"), pickle.dumps({}))

        # head file, where current commit hash is stored
        write_file(os.path.join(self.main_folder, repo_id, "refs/head", "main"), "", binary_=False)

        # Write the current branch to the HEAD file. default: main branch
        write_file(os.path.join(self.main_folder, repo_id, "HEAD"), "ref: refs/head/main", binary_=False)
