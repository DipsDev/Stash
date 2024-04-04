import os
import zlib

from filelock import FileLock

from models.tree import Tree


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


def read_file(path, binary_=True) -> bytes | str:
    """Reads a binary file"""
    with open(path, "rb" if binary_ else "r") as f:
        return f.read()


def resolve_object(main_folder, repo_id, sha1) -> bytes:
    """Returns the bytes of an object"""
    path = resolve_object_location(main_folder, repo_id, sha1)
    return bytes(read_file(path, binary_=True))


def resolve_object_location(full_repo, repo_id, obj_hash):
    """resolves an object hash to its path on the disk"""
    allowed_path = os.path.join(full_repo, repo_id)
    pth = os.path.join(full_repo, repo_id, "objects", obj_hash[:2], obj_hash[2:])
    if is_directory_traversal(allowed_path, pth):
        print("Directory traversal was executed.")
        quit(1)

    return pth


def is_directory_traversal(safe_dir: str, value: str):
    """Check if the user tried a directory traversal"""
    return os.path.commonprefix((os.path.realpath(value), safe_dir)) != safe_dir


class FileSystemProvider:
    def __init__(self, storage_path: str, repo_id: str):
        self.main_folder = storage_path
        self.repo_id = repo_id
        self.lock = FileLock(os.path.join(self.main_folder, repo_id, "lock"), timeout=5)

    def generate_prep_file(self, tree_hash: str):
        """
        Returns a preparefile for the given commit.
        prepfile contains all directories, subdirectories and files that the commit contains.
        """
        tree_data_encoded = resolve_object(self.main_folder, self.repo_id, tree_hash)
        tree = Tree.parse_tree(tree_data_encoded.decode())
        file = f"{tree_hash} tree\n"
        for key, obj in tree.items():
            if obj.get_type() == "tree":
                file += self.generate_prep_file(obj.get_hash())
            else:
                file += f"{obj.get_hash()} {obj.get_type()}\n"
        return file

    def generate_pack_file(self, prep_file: str):
        """Generates a packfile from a prep file
        prep files usually look like:

        sha1 type
        """
        pack_file = b""
        prep_file = prep_file.split("\n")
        del prep_file[-1]

        MAX_DIGIT_SIZE = 8  # 12mb
        for row in prep_file:
            sha, obj_type = row.split(" ")
            loc = resolve_object_location(self.main_folder, self.repo_id, sha)
            data = bytes(read_file(loc, binary_=True))
            pack_file += f"{sha} {str(len(data)).zfill(MAX_DIGIT_SIZE)}".encode() + data + "\n".encode()

        return zlib.compress(pack_file)

    def execute_packfile(self, pack_file: bytes) -> (str, bytes):
        """
        Decompiles the packfile, to usable form

        {sha (40 bytes)} {data_length}{data}

        """
        index = 0
        MAX_DIGIT_SIZE = 8  # 12mb

        self.lock.acquire()
        try:
            while index < len(pack_file):
                sha1 = pack_file[index:index + 40].decode()  # Extract SHA1 hash
                index += 41
                data_length = int(pack_file[index:index + MAX_DIGIT_SIZE].decode())
                index += MAX_DIGIT_SIZE
                data_content = pack_file[index:index + data_length]  # Extract data
                index += data_length + 1  # Move index to the next line
                self.create_object(sha1, data_content)
        finally:
            self.lock.release()

    def create_object(self, sha: str, compressed_data: bytes):
        """Creates an object in the objects database"""
        pth = resolve_object_location(self.main_folder, self.repo_id, sha)
        if not os.path.exists(pth):
            folder_path = os.path.join(self.main_folder, self.repo_id, "objects", sha[:2])
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            write_file(pth, compressed_data, binary_=True)

    def get_server_object(self, s: str, c: str):
        """Fetch a web_server object from a remote repository"""
        assert len(s) == 2
        assert len(c) == 38

        if not os.path.exists(os.path.join(self.main_folder, self.repo_id, "objects", s, c)):
            return None

        obj = resolve_object(self.main_folder, self.repo_id, f"{s}{c}")
        return obj

    def get_repo_branches(self) -> list[str]:
        """Gets the branches available in a repository"""
        return os.listdir(os.path.join(self.main_folder, self.repo_id, "refs", "head"))

    def get_head_commit(self, branch: str):
        """Gets the current head commit"""
        head_commit_path = os.path.join(self.main_folder, self.repo_id, "refs/head", branch)
        if not os.path.exists(head_commit_path):
            return None

        with self.lock:
            if not os.path.exists(head_commit_path):
                return None
            cmt = read_file(head_commit_path, binary_=False)
            return cmt

    def update_head_commit(self, branch: str, new_head: str):
        """Updates the current head commit"""
        head_path = os.path.join(self.main_folder, self.repo_id, "refs", "head", branch)

        with self.lock:
            write_file(head_path, new_head, binary_=False)

    def extract_commit_data(self, sha1) -> tuple:
        """Extracts the commit data, given its hash value"""
        cmt = resolve_object(self.main_folder, self.repo_id, sha1).decode()
        lines = cmt.split("\n")
        del lines[2]

        assert lines[0][0:6] == "parent"
        parent_hash = lines[0][7::]

        assert lines[1][0:4] == "tree"
        tree_hash = lines[1][5::]

        message = lines[2]

        return message, tree_hash, parent_hash

    def get_current_commit_files(self, branch_name="main") -> (str, list[()]):
        """Returns a list of the current commit file names"""
        last_commit = self.get_head_commit(branch_name)
        if last_commit == "":
            return []

        message, tree_hash, parent = self.extract_commit_data(last_commit)

        # Traverse tree hash
        tree_view = self.get_server_object(tree_hash[:2], tree_hash[2:]).decode().split("\n")
        tree_view.pop()  # Remove blank line

        files_commit = []
        for row in tree_view:
            tp, hsh, filename = row.split(" ")
            files_commit.append((tp, hsh, filename))
        return message, files_commit
