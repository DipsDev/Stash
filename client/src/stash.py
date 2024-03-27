"""
Main class
"""
import os
import pickle
import sys

import objects
from handlers import cli_parser
from handlers.branch_handler import BranchHandler
from handlers.commit_handler import CommitHandler
from handlers.logger_handler import Logger, ColorCode
from handlers.remote_connection_handler import RemoteConnectionHandler
from objects import read_file, write_file


def load_ignore_file(path: str):
    """Loads an ignore file, to a dictionary"""
    if not os.path.isdir(path):
        raise Exception("'path' must be a valid dictionary.")
    ignore_path = os.path.join(path, ".stashignore")
    d = {}
    if os.path.exists(ignore_path):
        with open(ignore_path, "r") as f:
            for line in f.read().splitlines():
                d[line] = True

    return d


class Stash:
    """The main stash class"""

    def __init__(self, folder_path, print_mode_=False):
        self.folder_path = folder_path
        self.print_mode = print_mode_

        if not os.path.exists(self.folder_path):
            raise FileNotFoundError("stash: couldn't find repository folder.")

        self.repo_path = os.path.join(folder_path, ".stash")
        self.initialized = os.path.exists(self.repo_path)
        # self.stash_actions = Actions(folder_path, self.remote_handler)

        # Register handlers
        self.remote_handler = RemoteConnectionHandler(full_repo=self.repo_path)
        self.commit_handler = CommitHandler(self.folder_path, self.repo_path, self.remote_handler)
        self.branch_handler = BranchHandler(self.folder_path, self.commit_handler)

        self.current_branch_ref = "refs/head/main"
        self.branch_name = "main"
        if os.path.exists(os.path.join(self.repo_path, "HEAD")):
            unmod_ref = read_file(os.path.join(self.repo_path, "HEAD"), binary_=False)
            self.current_branch_ref = unmod_ref.split(" ")[1]  # ref: refs/head/main
            self.branch_name = self.current_branch_ref.split("/")[-1]

    @cli_parser.register_command(0)
    def init(self):
        """
        Create an empty Stash repository or reinitialize an existing one
        stash init

        Description:
            Initializes the repository and creates needed objects.
            This command must be used before using any other command, and will throw an error if not.

        Flags:
            None

        """
        if self.initialized:
            print("stash: repository is initialized, use 'stash help'.")
            return

        os.mkdir(self.repo_path)
        # create the required folders for the database
        for name in ["objects", "index", "refs", "refs/head"]:
            os.mkdir(os.path.join(self.repo_path, name))

        # create the required files
        # indices file, where file indexes are stored
        write_file(os.path.join(self.repo_path, "index", "d"), pickle.dumps({}))

        # head file, where current commit hash is stored
        write_file(os.path.join(self.repo_path, "refs/head", "main"), "", binary_=False)

        # Write the current branch to the HEAD file. default: main branch
        write_file(os.path.join(self.repo_path, "HEAD"), "ref: refs/head/main", binary_=False)

        if not self.print_mode:
            Logger.println(f'stash: initialized empty repository at {self.folder_path}.')
            self.initialized = True  # Important for tests

    @cli_parser.register_command(1)
    def commit(self, message: str):
        """
        Record changes to the repository
        stash commit <message>

        Description:
            Records local changes to the repository.
            This command may be used before pushing the changes to the remote server.

        Flags:
            None

        Examples:
            'stash commit "Initial Commit"'
                Records the changes to the current working repository.
        """
        if not self.initialized:
            Logger.println("stash: repository isn't initialized, use 'stash init'.")
            return ""

        cmt_hash = self.commit_handler.commit(message=message, branch_name=self.branch_name)
        if self.print_mode:
            return cmt_hash

        Logger.highlight("stash: changes were committed")
        return cmt_hash

    @cli_parser.register_command(0)
    def push(self):
        """
        Update remote refs along with associated objects
        stash push

        Description:
            Updates remote refs and sends associated objects.
            You'll be prompted to enter repository fingerprint and correlated password.
            All changes will be shown in the stash webserver.


        Flags:
            None
        """
        if not self.initialized:
            Logger.println("stash: repository isn't initialized, use 'stash init'.")
            return

        current_commit = self.commit_handler.get_head_commit(self.branch_name)
        assert current_commit != ""

        # fetch the current commit from the web_server
        # find_diff between the current local version and remote version
        # send the diff files
        self.remote_handler.connect()
        prep_file = self.commit_handler.find_diff(current_commit, "", True)
        pack_file = self.remote_handler.generate_pack_file(prep_file)
        self.remote_handler.push_pkt("stash-send-packfile", pack_file)
        d = self.remote_handler.push_pkt("stash-update-head", self.commit_handler.get_head_commit("main"))
        print(d)
        self.remote_handler.close()

    @cli_parser.register_command(1)
    def merge(self, wanted_branch: str):
        """
        Join two or more development histories together
        stash merge <branch_name>

        Description:
            Joins two development branches together.
            Merging has two ways of merging: Fast-Forward and Three-Way Merge.
            Conflicts between the two branches might be thrown. if that's the case, conflicts must be solved manually.

        Flags:
            None
        """
        if self.branch_name == wanted_branch:
            Logger.println("stash: cannot merge between two exact branches.")
            exit(1)

        if self.branch_handler.can_fast_forward(self.branch_name, wanted_branch):
            Logger.custom("Fast Forward:", ColorCode.CITALIC)
            self.branch_handler.local_fast_forward_merge(self.branch_name, wanted_branch)

        else:
            Logger.custom("Three Way Merge: ", ColorCode.CITALIC)
            self.branch_handler.local_three_way_merge(self.branch_name, wanted_branch)
        Logger.highlight(f"stash: Successfully merged branches. {wanted_branch} -> {self.branch_name}")

    @cli_parser.register_command(-1)
    def branch(self, params: str, flags: dict):
        """
        List, create, or delete branches
        stash branch [-d] [<branch_name>]

        Description:
            Creates or deletes a branch.
            If no <branch_name> was provided, stash will display all available branches, as well as the current working one.
            This command CANNOT be used to switch branches. for switching, use stash checkout.

        Flags:
            -d <existing_branch>
            Deletes the branch with the name <branch_name>. cannot be used if this is the currently working branch.
        """
        if not self.initialized:
            Logger.println("stash: repository isn't initialized, use 'stash init'.")
            return

        if len(params) == 0:
            branches = self.branch_handler.get_all_branches()
            for branch in branches:
                if branch == self.branch_name:
                    Logger.highlight(f"* {branch}")
                else:
                    Logger.println(f"{branch}")
            exit(1)

        if flags.get("d"):
            # Delete Branch
            if params[0] == self.branch_name:
                Logger.println("stash: cannot delete current working branch, please switch before deleting.")
                exit(1)

            self.branch_handler.delete_branch(branch_name=params[0])
            Logger.highlight(f"stash: branch '{params[0]}' was successfully deleted.")
            exit(1)

        self.branch_handler.create_branch(params[0],
                                          last_commit_sha=self.commit_handler.get_head_commit(self.branch_name))
        Logger.highlight("stash: new branch created.")

    @cli_parser.register_command(1)
    def add(self, filename: str):
        """
        Add file contents to the index
        stash add <filename / folder>

        Description:
            Adds given file or folder contents to the index. can be provided with a relative to a folder (ex: '.').
            Create a .stashignore file in a folder to restrict adding of some files inside the same folder, or other nested ones.

        Flags:
            None

        Examples:
            'stash add .'
                Adds all files in the current directory.

            'stash add files'
                Adds all files in the 'files' directory.

        """
        if not self.initialized:
            Logger.println("stash: repository isn't initialized, use 'stash init'.")
            return

        path = os.path.join(self.folder_path, filename)
        path = os.path.normpath(path)
        # Get the index database
        if not os.path.exists(path):
            print("stash: No file was found. Please check your spelling.")
            exit(1)

        index_path = os.path.join(self.repo_path, "index", "d")
        # Load the database
        indices = pickle.loads(objects.read_file(index_path))

        files_added = 1

        if os.path.isdir(path):
            def traverse_dirs(p, ignores=None):
                if ignores is None:
                    ignores = {}
                b = [p]
                ignores.update(load_ignore_file(p))
                for entry in os.scandir(p):
                    if ignores.get(entry.name) is not None:
                        continue
                    if entry.name.startswith(".stash"):
                        continue
                    if entry.is_dir():
                        b.extend(traverse_dirs(entry.path, ignores))
                    b.append(entry.path)
                return b

            buffer = traverse_dirs(path)
            files_added = len(buffer) - 1
            for i in buffer:
                indices[i] = True

        else:
            indices[os.path.dirname(path)] = True
            indices[path] = True

        write_file(index_path, pickle.dumps(indices))

        if not self.print_mode:
            Logger.highlight(f"stash: added {files_added} file(s) to the local repository.")

    @cli_parser.register_command(1)
    def clone(self, repo_fingerprint: str):
        """
        Clone a repository into a new directory
        stash clone <repository_fingerprint> [local_path]

        Description:
            Clones a remote repository, into a given directory.:
            if [local_path] is undefined, it uses the current working directory instead.
            <repository_fingerprint> should be in the following format: author_username@repositry_name

        Flags:
            None:

        Examples:
            'stash clone gamer@helloworld'
                Clones the repository 'helloworld', created by user 'gamer', to the current working directory.

        """

        # Fetch main branch from 

    @cli_parser.register_command(1)
    def checkout(self, branch_name: str, upsert=False):
        """
        Switch branches or restore working tree files
        stash checkout [-b] <branch>

        Description:
            Switches branches or restores working tree files.
            if some unwanted files were deleted, you may use this command to restore to the last branch commit.

        Flags:
            -b <new_branch>
            Create a new branch named <new_branch> and switch to it;

        Examples:
            'stash checkout -b dev'
                Creates a 'dev' branch, and switches to it

        """
        if not self.initialized:
            Logger.println("stash: repository isn't initialized, use 'stash init'.")
            return

        branch_exists = os.path.exists(os.path.join(self.repo_path, "refs/head", branch_name))
        if not branch_exists and not upsert:
            Logger.println(f"stash: branch does not exist. run 'checkout -b {branch_name}' to create a new branch.")
            return

        # Create the branch if not exists
        if not branch_exists and upsert:
            self.branch_handler.create_branch(branch_name, self.commit_handler.get_head_commit(self.branch_name))

        write_file(os.path.join(self.repo_path, "HEAD"),
                   f"ref: refs/head/{branch_name}", binary_=False)

        if branch_exists:
            self.branch_handler.load_branch(branch_name)

        self.current_branch_ref = f"ref: refs/head/{branch_name}"  # Important for tests
        self.branch_name = branch_name

        Logger.highlight(f"stash: switched branch, now in '{branch_name}'.")
