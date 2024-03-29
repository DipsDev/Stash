"""
Module for testing the branching functionallity
"""
import os.path
import pickle
import tempfile
import unittest
import shutil

import utils
from client.src.stash import Stash
from handlers.logger_handler import Logger, TestPrinter
from utils import generate_random_filename, write_pseudo_data


class BranchingTest(unittest.TestCase):
    """Test branching. merging, branching, and checking out."""

    test_dir_path = None
    stash = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir_path = tempfile.mkdtemp()
        cls.stash = Stash(cls.test_dir_path)
        cls.stash.init()
        Logger.set_printer(TestPrinter())

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.test_dir_path)

    def test_one_file_adding(self):
        """Should be able to add one file to the index"""
        file_name = generate_random_filename()

        write_pseudo_data(os.path.join(self.stash.folder_path, file_name))

        self.stash.add(file_name)
        with open(os.path.join(self.stash.repo_path, "index", "d"), "rb") as f:
            data = pickle.load(f)
            self.assertIn(os.path.join(self.stash.folder_path, file_name), data)

    def test_nested_file(self):
        """Should be able to add a nested file"""
        folder_path = os.path.join(self.stash.folder_path, utils.generate_random_filename("folder"))
        os.mkdir(folder_path)

        nested_filename_1 = os.path.join(folder_path, utils.generate_random_filename())
        write_pseudo_data(nested_filename_1)

        nested_filename_2 = os.path.join(folder_path, utils.generate_random_filename())
        write_pseudo_data(nested_filename_2)

        self.stash.add(nested_filename_1)
        self.stash.add(nested_filename_2)

        with open(os.path.join(self.stash.repo_path, "index", "d"), "rb") as f:
            data = pickle.load(f)
            self.assertIn(nested_filename_1, data)
            self.assertIn(nested_filename_2, data)

    def test_folder_adding(self):
        """Should be able to add an entire folder"""
        folder_path = os.path.join(self.stash.folder_path, utils.generate_random_filename("folder"))
        os.mkdir(folder_path)

        nested_filename_1 = os.path.join(folder_path, utils.generate_random_filename())
        write_pseudo_data(nested_filename_1)

        nested_filename_2 = os.path.join(folder_path, utils.generate_random_filename())
        write_pseudo_data(nested_filename_2)

        self.stash.add(folder_path)

        with open(os.path.join(self.stash.repo_path, "index", "d"), "rb") as f:
            data = pickle.load(f)
            self.assertIn(nested_filename_1, data)
            self.assertIn(nested_filename_2, data)

    def test_global_ignore_file(self):
        """Should ignore all files listed in .stashignore file"""
        filename_1 = os.path.join(self.stash.folder_path, utils.generate_random_filename())
        write_pseudo_data(filename_1)

        filename_2 = os.path.join(self.stash.folder_path, utils.generate_random_filename())
        write_pseudo_data(filename_2)

        with open(os.path.join(self.stash.folder_path, ".stashignore"), "w") as f:
            f.write(os.path.basename(filename_2))

        nested_folder = os.path.join(self.stash.folder_path, utils.generate_random_filename("folder"))
        os.mkdir(nested_folder)
        nested_file = os.path.join(nested_folder, os.path.basename(filename_2))
        write_pseudo_data(nested_file)

        self.stash.add(".")

        with open(os.path.join(self.stash.repo_path, "index", "d"), "rb") as f:
            data = pickle.load(f)
            self.assertIn(filename_1, data)
            self.assertNotIn(filename_2, data)
            self.assertNotIn(filename_2, data)
            self.assertNotIn(nested_file, data)
            self.assertNotIn(".stashignore", data)

    def test_folder_ignore(self):
        """Should ignore all files listed in .stashignore file"""
        folder_path = os.path.join(self.stash.folder_path, "folder")
        os.mkdir(folder_path)

        filename_1 = os.path.join(folder_path, utils.generate_random_filename())
        write_pseudo_data(filename_1)

        with open(os.path.join(self.stash.folder_path, ".stashignore"), "w") as f:
            f.write("folder")

        self.stash.add(".")

        with open(os.path.join(self.stash.repo_path, "index", "d"), "rb") as f:
            data = pickle.load(f)

            self.assertNotIn(folder_path, data)
            self.assertNotIn(filename_1, data)
            self.assertNotIn(".stashignore", data)


if __name__ == "__main__":
    unittest.main()
