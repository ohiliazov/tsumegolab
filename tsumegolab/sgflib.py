import re
from collections import OrderedDict
from pathlib import Path
from typing import Iterable

reCharsToEscape = re.compile(r"([]\\])")  # characters that need to be \escaped
reGameTreeStart = re.compile(r"\s*\(")
reGameTreeEnd = re.compile(r"\s*\)")
reNodeStart = re.compile(r"\s*;")
reEscape = re.compile(r"\\")
reLineBreak = re.compile(r"\r\n?|\n\r?")  # CR, LF, CR/LF, LF/CR
rePropertyLabel = re.compile(r"\s*([A-Za-z]+)\s*(?=\[)")
rePropertyStart = re.compile(r"\s*\[")
rePropertyEnd = re.compile(r"]")


def escape_text(text: str) -> str:
    return reCharsToEscape.sub(r"\\\1", text)


def convert_control_chars(text):
    """Converts control characters in [text] to spaces. Override for variant behaviour."""
    return text.translate(
        str.maketrans(
            "\000\001\002\003\004\005\006\007\010\011\013\014\016\017\020"
            "\021\022\023\024\025\026\027\030\031\032\033\034\035\036\037",
            " " * 30,
        )
    )


class ParserError(Exception):
    """Raised by SGFParser"""


class GameTreeIndexError(Exception):
    """Raised by `GameTree.get_subtree()`"""


class GameTreeNavigationError(Exception):
    """Raised by `Cursor.next()`."""


class SGFPropValues(list[str]):
    def __init__(self, items: Iterable = ()):
        super().__init__(map(str, items))

    def __str__(self) -> str:
        return "[" + "][".join(map(escape_text, self)) + "]"


class SGFNode(OrderedDict[str, SGFPropValues]):
    def __setitem__(self, key, value: list[str]):
        super().__setitem__(key, SGFPropValues(value))

    def __str__(self):
        return ";" + "".join([key + str(value) for key, value in self.items()])

    def pretty(self, indent: int = 0, max_length: int = 79):
        if len(str(self)) + indent < max_length:
            return " " * indent + str(self)

        pretty_str = " " * indent + ";"
        for key, value in self.items():
            pretty_str += "\n" + " " * indent + key + str(value)
        return pretty_str

    def get_move(self) -> tuple[str, SGFPropValues] | None:
        if "B" in self:
            return "B", self["B"]
        if "W" in self:
            return "W", self["W"]


class SGFTree:
    def __init__(
        self,
        trunk: list[SGFNode] = None,
        leaves: list["SGFTree"] | None = None,
    ):
        self.trunk = [SGFNode(item) for item in trunk or []]
        self.leaves = [
            SGFTree(item.trunk, item.leaves) for item in leaves or []
        ]

    def __str__(self) -> str:
        sgf_str = "("
        for item in self.trunk:
            sgf_str += str(item)

        for item in self.leaves:
            sgf_str += str(item)

        sgf_str += ")"
        return sgf_str

    def pretty(self, indent: int = 0, max_length: int = 79) -> str:
        if len(str(self)) + indent < max_length:
            return " " * indent + str(self) + "\n"

        pretty_str = " " * indent + "(\n"

        for node in self.trunk:
            pretty_str += node.pretty(indent + 2, max_length) + "\n"

        for leaf in self.leaves:
            pretty_str += leaf.pretty(indent + 2, max_length)
        pretty_str += " " * indent + ")\n"

        return pretty_str

    def __getitem__(self, item) -> SGFNode:
        return self.trunk[item]

    def __len__(self) -> int:
        return len(self.trunk)

    def mainline(self) -> "SGFTree":
        trunk = self.trunk

        if self.leaves:
            trunk += self.leaves[0].mainline().trunk

        return SGFTree(trunk)

    def append_node(self, node: SGFNode):
        self.trunk.append(node)

    def insert_tree(self, index: int, tree: "SGFTree"):
        if index < 1:
            raise GameTreeIndexError("cannot insert to root node")

        if index < len(self.trunk):
            self.trunk = self.trunk[:index]
            self.leaves = [
                SGFTree(self.trunk[index:], self.leaves),
                tree,
            ]
        elif self.leaves:
            self.leaves.append(tree)
        else:
            self.trunk += tree.trunk
            self.leaves = tree.leaves

        return self


class Cursor:
    def __init__(self, tree: SGFTree):
        self.tree = self.root = tree
        self.index = 0

        self._stack = []

    @property
    def current_node(self):
        return self.tree[self.index]

    def get_trunk(self) -> SGFTree:
        trunk = SGFTree()

        for tree in self._stack:
            for node in tree:
                trunk.append_node(node)

        for node in self.tree.trunk[: self.index + 1]:
            trunk.append_node(node)

        return trunk

    def next(self, leaf_number: int = 0) -> SGFNode:
        if self.index + 1 < len(self.tree):  # more main line?
            if leaf_number != 0:
                raise GameTreeNavigationError("still on trunk")
            self.index += 1
        elif self.tree.leaves:  # variations exist?
            if leaf_number < len(self.tree.leaves):
                self._stack.append(self.tree)
                self.tree = self.tree.leaves[leaf_number]
                self.index = 0
            else:
                raise GameTreeNavigationError("no such leaf")
        else:
            raise GameTreeNavigationError("reached tree end")

        return self.current_node

    def previous(self) -> SGFNode:
        if self.index > 0:  # more main line?
            self.index -= 1
        elif self._stack:  # were we in a variation?
            self.tree = self._stack.pop()
            self.index = len(self.tree) - 1
        else:
            raise GameTreeNavigationError("reached tree start")

        return self.current_node


class SGFParser:
    def __init__(self, data: str):
        self.data = data
        self.index = 0

    @classmethod
    def from_file(cls, path: Path):
        with open(path) as f:
            return cls(f.read())

    def _consume_regex(self, pattern: re.Pattern):
        if m := pattern.match(self.data, self.index):
            self.index = m.end()
        return m

    def parse_collection(self) -> list[SGFTree]:
        """
        Parses trees between matching '(' and ')'.
        Example: (;AB[dd][ee]B[aa](;W[ab];B[bb])(;W[ba]))
        index                     ^                     ^
                              start                     end
        """
        trees = []

        while self._consume_regex(reGameTreeStart):
            trees.append(self.parse_tree())

        return trees

    def parse_tree(self) -> SGFTree:
        """
        Parses single after '(' and matching ')'.
        Example: (;AB[dd][ee]B[aa](;W[ab];B[bb])(;W[ba]))
        index                      ^            ^
                               start            end
        """
        trunk = []
        while self._consume_regex(reNodeStart):
            trunk.append(self._parse_node())

        if not trunk:
            raise ParserError("empty tree")

        leaves = self.parse_collection()
        self._consume_regex(reGameTreeEnd)

        return SGFTree(trunk, leaves)

    def _parse_node(self) -> SGFNode:
        """
        Parses single node after consuming ';'.
        Example: (;AB[dd][ee]B[aa](;W[ab];B[bb])(;W[ba]))
        index      ^              ^
               start              end
        """
        node = SGFNode()
        while m := self._consume_regex(rePropertyLabel):
            node[m.group(1)] = self._parse_property_values()

        if not node:
            raise ParserError("empty node")

        return node

    def _parse_property_values(self) -> SGFPropValues:
        """
        Parses property values between opening '[' and closing ']'.
        Example: (;AB[dd][ee]B[aa](;W[ab];B[bb])(;W[ba]))
        index         ^      ^
                  start      end
        """
        pv_list = SGFPropValues()

        while self._consume_regex(rePropertyStart):
            pv_list.append(self._parse_property_value())

        if not pv_list:
            raise ParserError(f"empty property at char {self.index}")

        return pv_list

    def _parse_property_value(self) -> str:
        """
        Parses single property value between opening '[' and closing ']'.
        Example: (;AB[dd][ee]B[aa](;W[ab];B[bb])(;W[ba]))
        index         ^  ^
                  start  end
        """
        value = ""
        while not self._consume_regex(rePropertyEnd):
            if self._consume_regex(reEscape):
                if not self._consume_regex(reLineBreak):
                    value += self.data[self.index - 1]
            value += self.data[self.index]
            self.index += 1

        return convert_control_chars(value)
