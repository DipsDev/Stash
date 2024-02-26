"""
Module that represents a main

TODO: delete before production
"""
import os.path
import shutil
import tempfile

from stash import Stash

temp_dir = tempfile.mkdtemp()
print(f"Generated a new temp folder {temp_dir}")

ac = Stash(temp_dir, test_mode_=True)

ac.init()

with open(os.path.join(temp_dir, "text.txt"), "w", encoding="utf-8") as f:
    f.write("Hello World")

ac.add("text.txt")

os.mkdir(os.path.join(temp_dir, "myfolder"))

with open(os.path.join(temp_dir, "myfolder", "secret"), "w", encoding="utf-8") as f:
    f.write("This is my secret: I love dogs")

ac.add("./myfolder/secret")

F1 = ac.commit("Initial Commit")

with open(os.path.join(temp_dir, "abc.txt"), "w", encoding="utf-8") as f:
    f.write("Hello World Again!")

ac.add("abc.txt")

F2 = ac.commit("Second commit")

with open(os.path.join(temp_dir, "abc.txt"), "w", encoding="utf-8") as f:
    f.write("Hello World Again!!")

with open(os.path.join(temp_dir, "myfolder", "secret"), "w", encoding="utf-8") as f:
    f.write("This is my secret: I love cats")

shutil.rmtree(os.path.join(temp_dir, "myfolder"))
F3 = ac.commit("Third commit")

ac.stash_actions.commit_handler.find_diff(F2, F3)

shutil.rmtree(temp_dir)
