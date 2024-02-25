"""
Module for testing the init action
"""
import os.path
import shutil
import tempfile
import unittest

from client.src.stash import Stash


class InitAction(unittest.TestCase):
    """A class that __tests__ the init function, found in actions.py"""

    def setUp(self) -> None:
        self.test_dir_location = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir_location)

    def test_default_init(self):
        """Should work with normal parameters"""
        stash = Stash(self.test_dir_location)
        stash.init()
        self.assertTrue(os.path.exists(os.path.join(self.test_dir_location, ".stash")))

    def test_invalid_path(self):
        """Should throw an error if path does not exist"""
        with self.assertRaises(FileNotFoundError):
            Stash(os.path.join(self.test_dir_location, "thisdoesnotexist"))
