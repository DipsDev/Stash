import os


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


class FileSystem:

    def __init__(self, storage_path: str):
        self.main_folder = storage_path

    def get_repo_branches(self, repo_id: str) -> list:
        """Gets the branches availiable in a repository"""
        return os.listdir(os.path.join(self.main_folder, repo_id, "refs", "head"))

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
