import sys

import requests

from models.commit import Commit


class RemoteConnectionHandler:
    """Handles remote repository connections, and provides useful functions."""

    def __init__(self, url: str):
        self.repo_url = url.rstrip("/")
        self.request_headers = {
            'Authorization': "Bearer 1a2ef8ac832a2a93f0dc4b25242fe6132498b09f65450a7091a5dbd022733dd4"
        }

    def get_remote_head_commit(self, branch: str):
        """Get remote head commit"""
        cmp_url = f"{self.repo_url}/{branch}/head"
        r = requests.get(url=cmp_url, headers=self.request_headers)
        if r.status_code != 200:
            print(f"stash: Couldn't access remote repository. Reason: {r.reason} {r.status_code}")
            sys.exit(1)
        return r.text

    def resolve_remote_object(self, sha1: str):
        """Resolve a remote object"""
        cmp_url = f"{self.repo_url}/objects/{sha1[:2]}/{sha1[2:]}"
        r = requests.get(url=cmp_url, headers=self.request_headers)
        if r.status_code != 200:
            print(f"stash: Couldn't access remote repository. Reason: {r.reason} {r.status_code}")
            sys.exit(1)
        return r.text

    def resolve_remote_commit_data(self, sha1):
        cmt = self.resolve_remote_object(sha1)
        lines = cmt.split("\n")
        del lines[2]

        assert lines[0][0:6] == "parent"
        parent_hash = lines[0][7::]

        assert lines[1][0:4] == "tree"
        tree_hash = lines[1][5::]

        message = lines[2]

        return Commit(message, tree_hash=tree_hash, parent=parent_hash)
