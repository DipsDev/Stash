"""
Module that represents a main

TODO: delete before production
"""
import tempfile
from stash import Stash

temp_dir = tempfile.mkdtemp()
print(f"Generated a new temp folder {temp_dir}")


ac = Stash(temp_dir)

ac.push()

ac.checkout("main")

ac.push()
