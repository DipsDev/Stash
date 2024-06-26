import os
import zlib

from filelock import FileLock


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


def is_directory_traversal(safe_dir: str, value: str):
    """Check if the user tried a directory traversal"""
    if os.path.commonprefix((os.path.realpath(value), safe_dir)) != safe_dir:
        return True
    return False


class FileSystem:

    def __init__(self, storage_path: str):
        self.main_folder = storage_path

    def craft_lock(self, repo_id: str):
        return FileLock(os.path.join(self.main_folder, repo_id, "lock"), timeout=3)

    def get_server_object(self, repo_id: str, s: str, c: str):
        """Fetch a web_server object from a remote repository"""
        assert len(s) == 2
        assert len(c) == 38
        if not os.path.exists(os.path.join(self.main_folder, repo_id, "objects", s, c)):
            return None

        if is_directory_traversal(os.path.join(self.main_folder, repo_id),
                                  os.path.join(self.main_folder, repo_id, "objects", s, c)):
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

        repo_lock = self.craft_lock(repo_id)

        with repo_lock:
            cmt = read_file(head_commit_path, binary_=False)
            return cmt

    def set_head_commit(self, repo_id: str, branch: str, hash: str):
        """Gets the current head commit"""
        head_commit_path = os.path.join(self.main_folder, repo_id, "refs/head", branch)
        if not os.path.exists(head_commit_path):
            return None

        repo_lock = self.craft_lock(repo_id)

        with repo_lock:
            write_file(head_commit_path, hash, binary_=False)

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

    def get_nested_tree_contents(self, repo_id: str, tree_path: str, branch_name="main"):
        """
        Traverses the content of a tree
        Returns None if no file was found
        Returns tree, and tree contents,
        Returns blob, and blob hash
        """
        last_commit = read_file(os.path.join(self.main_folder, repo_id, "refs/head", branch_name), binary_=False)
        if last_commit == "":
            return None

        message, tree_hash, parent = self.extract_commit_data(repo_id, last_commit)
        # Traverse tree hash
        return self.traverse_tree(repo_id, tree_hash, tree_path.split("/"))

    def traverse_tree(self, repo_id: str, sha1: str, target_path: list[str], current_path="", path_index=0):
        """Traverses a tree"""

        tree_view = self.get_server_object(repo_id, sha1[:2], sha1[2:]).decode().split("\n")
        tree_view.pop()
        calc_path = os.path.join(*target_path[:path_index + 1])

        if current_path == calc_path:
            tree_files = []
            for row in tree_view:
                tp, hsh, filename = row.split(" ")
                tree_files.append((tp, hsh, filename.replace("\\", "/")))
            return "tree", tree_files
        for row in tree_view:
            tp, hsh, filename = row.split(" ")
            if filename == calc_path:
                if tp == "tree":
                    return self.traverse_tree(repo_id, hsh, target_path,
                                              current_path=calc_path,
                                              path_index=path_index + 1)
                if tp == "blob":
                    print(hsh)
                    return "blob", hsh

        return None

    def get_current_commit_files(self, repo_id: str, branch_name="main") -> (str, list[()]):
        """Returns a list of the current commit file names"""
        last_commit = read_file(os.path.join(self.main_folder, repo_id, "refs/head", branch_name), binary_=False)
        if last_commit == "":
            return "", []

        message, tree_hash, parent = self.extract_commit_data(repo_id, last_commit)
        # Traverse tree hash
        tree_view = self.get_server_object(repo_id, tree_hash[:2], tree_hash[2:]).decode().split("\n")
        tree_view.pop()  # Remove blank line

        files_commit = []
        for row in tree_view:
            tp, hsh, filename = row.split(" ")
            files_commit.append((tp, hsh, filename))
        return message, files_commit

    def copy_latest_commit(self, from_id: str, to_id: str, branch_name="main"):
        """Copies the latest commit to another repository"""
        latest_cmt_hash = self.get_head_commit(from_id, branch_name)
        tree_hash = self.extract_commit_data(from_id, latest_cmt_hash)[1]

        object_location_to = os.path.join(self.main_folder, to_id, "objects")
        object_location_from = os.path.join(self.main_folder, from_id, "objects")

        # Add the commit data
        commit_data = read_file(os.path.join(object_location_from, latest_cmt_hash[:2], latest_cmt_hash[2:]))
        cmt_path = os.path.join(object_location_to, latest_cmt_hash[:2])
        if not os.path.exists(cmt_path):
            os.mkdir(cmt_path)
        write_file(os.path.join(object_location_to, latest_cmt_hash[:2], latest_cmt_hash[2:]), commit_data)

        # Add the first tree
        tree_data = read_file(os.path.join(object_location_from, tree_hash[:2], tree_hash[2:]))
        cmt_path = os.path.join(object_location_to, tree_hash[:2])
        if not os.path.exists(cmt_path):
            os.mkdir(cmt_path)
        write_file(os.path.join(object_location_to, tree_hash[:2], tree_hash[2:]), tree_data)

        def craft_objects(repo_id=from_id, current_hash=tree_hash):
            if current_hash == "":
                return

            current_tree_data = resolve_object(self.main_folder, repo_id, current_hash).decode()
            items = current_tree_data.split("\n")
            del items[-1]
            for i in items:
                tp, hsh, pth = i.split(" ")
                data = read_file(os.path.join(object_location_from, hsh[:2], hsh[2:]))
                if not os.path.exists(os.path.join(object_location_to, hsh[:2])):
                    os.mkdir(os.path.join(object_location_to, hsh[:2]))
                write_file(os.path.join(object_location_to, hsh[:2], hsh[2:]), data=data, binary_=True)

                if tp == "blob":
                    continue
                if tp == "tree":
                    print('continued')
                    craft_objects(repo_id, hsh)

        craft_objects()
        self.set_head_commit(to_id, branch=branch_name, hash=latest_cmt_hash)

    def allocate_repository(self, repo_id: str):
        """Allocates a new repository in the filesystem"""
        os.mkdir(os.path.join(self.main_folder, repo_id))

        with self.craft_lock(repo_id):
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
