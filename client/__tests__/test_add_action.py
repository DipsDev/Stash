"""
Module for testing the add action
"""
import os.path
import pickle
import shutil
import tempfile
import unittest

from client.src.stash import Stash


class AddAction(unittest.TestCase):
    """A class that __tests__ the init function, found in handlers.py"""

    stash = None
    test_dir_location = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir_location = tempfile.mkdtemp()
        cls.stash = Stash(cls.test_dir_location)
        cls.stash.init()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.test_dir_location)

    def test_default_func(self):
        """Should work with normal parameters"""
        with open(os.path.join(self.test_dir_location, "my_text.txt"), "w", encoding="utf-8") as f:
            f.write("Hello World!")

        self.stash.add("my_text.txt")

        with open(os.path.join(self.test_dir_location, ".stash", "index", "d"), "rb") as f:
            dicts = pickle.load(f)
        self.assertIn("my_text.txt", dicts)

    def test_nonexistent_file(self):
        """Should throw an error if file is nonexistent"""

        with self.assertRaises(FileNotFoundError):
            self.stash.add("this_is_not_existent.null")


if __name__ == '__main__':
    unittest.main()
