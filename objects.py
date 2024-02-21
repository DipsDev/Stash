# stash init
# stash add .
# stash commit
# stash push
import hashlib
import os
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


def read_file(path, binary_=True):
    """Reads a binary file"""
    with open(path, "rb" if binary_ else "r") as f:
        return f.read()


def create_tree(repo, files: dict):
    """Creates a new commit tree"""
    entries = []
    for it in os.scandir(repo):
        if it.name == ".stash":
            continue
        full_path = os.path.join(repo, it.name)
        if it.is_file():
            if it.name in files:
                sha1 = hash_object(repo, read_file(full_path))
                entries.append(sha1)
        else:
            create_tree(full_path, files)
    sha1 = hash_object(repo, "".join(entries).encode(), type_="tree")
    return sha1, entries


def hash_object(repo, data, type_="blob"):
    """
    Hashes an object and writes the data to the database
    """
    header = "{}{}".format(type_, len(data)).encode()
    full_data = header + b'\x00' + data
    sha1 = hashlib.sha1(full_data).hexdigest()
    path = os.path.join(repo, ".stash", "objects", sha1[:2], sha1[2:])
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    write_file(path, zlib.compress(data))
    return sha1
