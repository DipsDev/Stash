"""
Module that exports multi object related functions
"""
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


def read_file(path, binary_=True) -> bytes or str:
    """Reads a binary file"""
    with open(path, "rb" if binary_ else "r") as f:
        return f.read()


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
