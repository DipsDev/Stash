"""
Module for testing the branching functionallity
"""
import glob
import tempfile
import unittest
import shutil
import os

from client.src.stash import Stash
from handlers.logger_handler import Logger, TestPrinter


class BranchingTest(unittest.TestCase):
    """Test branching. merging, branching, and checking out."""

    def setUp(self) -> None:
        self.test_dir_path = tempfile.mkdtemp()
        self.stash = Stash(self.test_dir_path)
        self.stash.init()
        Logger.set_printer(TestPrinter())

    def tearDown(self) -> None:
        print(Logger.printer.get_std())
        shutil.rmtree(self.test_dir_path)

    def test_no_branch(self):
        """Test merging when there is no branch to merge to"""
        with open(os.path.join(self.test_dir_path, "test_file.txt"), "w") as f:
            f.write("This is my best test case!")

        with open(os.path.join(self.test_dir_path, "test_file2.txt"), "w") as f:
            f.write("This is my least good test case!")

        self.stash.add(".")

        self.stash.commit("Initial Commit")

        with self.assertRaises(SystemExit):
            self.stash.merge("not-exists")

    def test_simple_loading(self):
        """Should only have files that are relevant to the branch"""
        with open(os.path.join(self.test_dir_path, "all.txt"), "w") as f:
            f.write("This is my best test case!")

        self.stash.add(".")

        self.stash.commit("c1")

        self.stash.checkout("t", upsert=True)

        with open(os.path.join(self.test_dir_path, "only_t.txt"), "w") as f:
            f.write("This is my best test case!")

        self.stash.add(".")

        self.stash.commit("c2")

        self.stash.checkout("main")

        pth = os.path.join(self.test_dir_path, "only_t.txt")
        self.assertFalse(os.path.exists(pth))

    def test_folder_loading(self):
        """Should show only folder that are relevant"""

        os.mkdir(os.path.join(self.test_dir_path, "all"))

        with open(os.path.join(self.test_dir_path, "all", "nested_all.txt"), "w") as f:
            f.write("abcefg")

        self.stash.add(".")

        self.stash.commit("c1")

        self.stash.checkout("t", upsert=True)

        with open(os.path.join(self.test_dir_path, "all", "nested_t.txt"), "w") as f:
            f.write("ONLY T")

        os.mkdir(os.path.join(self.test_dir_path, "all", "only_t"))

        with open(os.path.join(self.test_dir_path, "all", "only_t", "nested_nested_t.txt"), "w") as f:
            f.write("ONLY T")

        self.stash.add(".")
        self.stash.commit("c2")

        self.stash.checkout('main')

        with open(os.path.join(self.test_dir_path, "all", "nested_main.txt"), "w") as f:
            f.write("ONLY T")

        files = [os.path.basename(f) for f in glob.glob(self.test_dir_path + '/**/*.txt', recursive=True)]
        self.assertListEqual(files, ["nested_all.txt", "nested_main.txt"])

        self.stash.checkout("t")
        files = [os.path.basename(f) for f in glob.glob(self.test_dir_path + '/**/*.txt', recursive=True)]
        self.assertListEqual(files, ["nested_all.txt", "nested_t.txt", "nested_nested_t.txt"])

    def test_fast_forward(self):
        """Should fast-forward"""

        # Generate some simple files
        with open(os.path.join(self.test_dir_path, "test_file.txt"), "w") as f:
            f.write("This is my best test case!")

        with open(os.path.join(self.test_dir_path, "test_file2.txt"), "w") as f:
            f.write("This is my least good test case!")

        self.stash.add(".")

        self.stash.commit("Initial Commit")

        # Switch branch

        self.stash.checkout("testing", upsert=True)

        # Add file and change existing file

        with open(os.path.join(self.test_dir_path, "test_file3.txt"), "w") as f:
            f.write("I AM THE BEST")

        # Change existing file
        with open(os.path.join(self.test_dir_path, "test_file.txt"), "w") as f:
            f.write("I LOVE THIS TEST CASE")

        self.stash.add(".")
        self.stash.commit("First commit in testing branch")

        self.stash.checkout("main")

        with open(os.path.join(self.test_dir_path, "test_file.txt"), "r") as f:
            self.assertEqual(f.readline(), "This is my best test case!")

        self.stash.merge("testing")

        self.assertListEqual([".stash", "test_file.txt", "test_file2.txt", "test_file3.txt"],
                             os.listdir(self.test_dir_path))

    def test_three_way_merge(self):
        """Should three_way merge"""

        # Generate some simple files
        with open(os.path.join(self.test_dir_path, "test_file.txt"), "w") as f:
            f.write("This is my best test case!")

        with open(os.path.join(self.test_dir_path, "test_file2.txt"), "w") as f:
            f.write("This is my least good test case!")

        self.stash.add(".")

        self.stash.commit("Initial Commit")

        # Switch branch

        self.stash.checkout("testing", upsert=True)

        # Add file and change existing file

        with open(os.path.join(self.test_dir_path, "test_file3.txt"), "w") as f:
            f.write("I AM THE BEST")

        # Change existing file
        with open(os.path.join(self.test_dir_path, "test_file.txt"), "w") as f:
            f.write("I LOVE THIS TEST CASE")

        self.stash.add(".")
        self.stash.commit("First commit in testing branch")

        self.stash.checkout("main")

        with open(os.path.join(self.test_dir_path, "test_file4.txt"), "w") as f:
            f.write("This is my least good test case!")

        self.stash.add('.')
        self.stash.commit("Second commit at main")

        self.stash.merge("testing")

        self.assertListEqual([".stash", "test_file.txt", "test_file2.txt", "test_file3.txt", "test_file4.txt"],
                             os.listdir(self.test_dir_path))

        # Check if merging after merging is avaliable
        self.stash.checkout("new_branch", upsert=True)
        with open(os.path.join(self.test_dir_path, "test_file5.txt"), "w") as f:
            f.write("Hello World!")

        self.stash.add('.')
        self.stash.commit("c3")

        self.stash.checkout("main")
        with open(os.path.join(self.test_dir_path, "test_file6.txt"), "w") as f:
            f.write("Hello World!")

        self.stash.add('.')
        self.stash.commit("c3")
        self.stash.merge("new_branch")

        self.assertListEqual(
            [".stash", "test_file.txt", "test_file2.txt", "test_file3.txt", "test_file4.txt", "test_file5.txt",
             "test_file6.txt"], os.listdir(self.test_dir_path))


if __name__ == "__main__":
    unittest.main()
