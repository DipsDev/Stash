"""
Module that exports multi object related functions
"""
import hashlib
import os
import zlib

from models.commit import Commit
from models.tree import Tree
from models.tree_node import TreeNode


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


def find_diff(cmt1: Commit, cmt2: Commit):
    """Find the diff between 2 commits"""
    print(cmt1, cmt2)


def create_tree(repo, files: dict, current_):
    """Creates a new commit tree"""
    entries = []
    for it in os.scandir(current_):
        if it.name == ".stash":
            continue
        full_path = os.path.join(current_, it.name)
        if it.is_file():
            if it.name in files:
                sha1 = hash_object(repo, read_file(full_path))
                leaf = TreeNode(full_path, sha1)
                entries.append(leaf)
        else:
            new_sha1, new_entries = create_tree(repo, files, full_path)
            entries.append(Tree(full_path, new_sha1, new_entries))

    final_str = ""
    for i in entries:
        final_str += f"{i.get_type()} {i.get_hash()} {i.get_path()}\n"

    sha1 = hash_object(repo, final_str.encode(), type_="tree")
    return sha1, entries


def hash_object(repo, data, type_="blob"):
    """
    Hashes an object and writes the data to the database
    """
    header = f"{type_}{len(data)}".encode()
    full_data = header + b'\x00' + data
    sha1 = hashlib.sha1(full_data).hexdigest()
    path = os.path.join(repo, ".stash", "objects", sha1[:2], sha1[2:])
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    write_file(path, zlib.compress(data))
    return sha1


def resolve_object(full_repo, sha1) -> bytes:
    """Returns the original content of an object"""
    path = resolve_object_location(full_repo, sha1)
    return zlib.decompress(bytes(read_file(path, binary_=True)))


def resolve_object_location(full_repo, obj_hash):
    """resolves an object hash to its path on the disk"""
    return os.path.join(full_repo, "objects", obj_hash[:2], obj_hash[2:])
