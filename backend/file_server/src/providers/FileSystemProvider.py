import os
import struct
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
    """Returns the bytes of an object"""
    path = resolve_object_location(main_folder, repo_id, sha1)
    return bytes(read_file(path, binary_=True))


def resolve_object_location(full_repo, repo_id, obj_hash):
    """resolves an object hash to its path on the disk"""
    return os.path.join(full_repo, repo_id, "objects", obj_hash[:2], obj_hash[2:])


class FileSystemProvider:

    def __init__(self, storage_path: str):
        self.main_folder = storage_path

    def execute_packfile(self, repo_id: str, pack_file: bytes) -> (str, bytes):
        """
        Decompiles the packfile, to usable form

        {sha (40 bytes)} {data_length}{data}

        """
        index = 0
        while index < len(pack_file):
            sha1 = pack_file[index:index + 40].decode()  # Extract SHA1 hash
            index += 41
            data_length = int(pack_file[index:index + 4].decode())
            index += 4
            data_content = pack_file[index:index + data_length]  # Extract data
            index += data_length + 1  # Move index to the next line
            self.create_object(repo_id, sha1, data_content)

    def create_object(self, repo_id: str, sha: str, compressed_data: bytes):
        """Creates an object in the objects database"""
        pth = resolve_object_location(self.main_folder, repo_id, sha)
        if not os.path.exists(pth):
            folder_path = os.path.join(self.main_folder, repo_id, "objects", sha[:2])
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            write_file(pth, compressed_data, binary_=True)

    def get_server_object(self, repo_id: str, s: str, c: str):
        """Fetch a web_server object from a remote repository"""
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

    def update_head_commit(self, repo_id: str, branch: str, new_head: str):
        """Updates the current head commit"""
        head_path = os.path.join(self.main_folder, repo_id, "refs", "head", branch)
        write_file(head_path, new_head, binary_=False)

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
