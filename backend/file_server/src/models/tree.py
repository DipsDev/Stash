import dataclasses


@dataclasses.dataclass
class TreeNode:
    path: str
    node_hash: str
    type_: str


class Tree:

    @classmethod
    def parse_tree(cls, tree_data: str) -> dict[str, TreeNode]:
        """Parse a tree"""
        parsing = {}
        splits = tree_data.split("\n")
        del splits[-1]
        prev = [d.split(" ") for d in splits]
        for i in prev:
            parsing[i[-1]] = TreeNode(path=i[-1], node_hash=i[1], type_=i[0])
        return parsing
