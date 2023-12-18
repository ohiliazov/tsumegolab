from pathlib import Path

import numpy as np

from tsumegolab.board import Board, Color
from tsumegolab.sgflib import SGFNode, SGFParser, SGFPropValues, SGFTree
from tsumegolab.utils.coord_utils import (
    int_to_gtp_coord,
    int_to_sgf_coord,
    sgf_to_int_coord,
)
from tsumegolab.utils.tsumego_utils import tsumego_frame


def sgf_to_initial_stones(path: Path | str):
    tsumego = tsumego_frame(sgf_root_to_board(path).board)

    initial_stones = []
    for coord in np.argwhere(tsumego == Color.BLACK):
        initial_stones.append(("B", int_to_gtp_coord(coord)))
    for coord in np.argwhere(tsumego == Color.WHITE):
        initial_stones.append(("W", int_to_gtp_coord(coord)))

    return initial_stones


def sgf_root_to_board(path: str | Path) -> Board:
    sgf_parser = SGFParser.from_file(Path(path))
    tree = sgf_parser.parse_collection()
    root_node = tree[0].trunk[0]
    size = root_node.get("SZ", ["19"])[0]

    if ":" in size:
        width, height = map(int, size.split(":"))
    else:
        height = width = int(size)

    arr = np.zeros((height, width))

    for coord in root_node.get("AB", []):
        arr[sgf_to_int_coord(coord)] = Color.BLACK

    for coord in root_node.get("AW", []):
        arr[sgf_to_int_coord(coord)] = Color.WHITE

    return Board(arr)


def make_root_node(board: np.ndarray) -> SGFNode:
    height, width = board.shape
    if height == width:
        sz_prop = SGFPropValues([f"{height}"])
    else:
        sz_prop = SGFPropValues([f"{width}:{height}"])

    ab_prop = []
    aw_prop = []
    for coord in np.argwhere(board):
        sgf_coord = int_to_sgf_coord(coord)
        if board[tuple(coord)] == Color.BLACK:
            ab_prop.append(sgf_coord)
        else:
            aw_prop.append(sgf_coord)

    return SGFNode(
        {
            "FF": SGFPropValues(["4"]),
            "CA": SGFPropValues(["UTF-8"]),
            "GM": SGFPropValues(["1"]),
            "SZ": SGFPropValues(sz_prop),
            "AP": SGFPropValues(["tsumegolab:0.1.0"]),
            "AB": SGFPropValues(ab_prop),
            "AW": SGFPropValues(aw_prop),
        }
    )


def save_board_to_sgf(board: Board, path: Path):
    if board.history:
        initial_board, *_ = board.history[0]
    else:
        initial_board = board.board

    tree = SGFTree([make_root_node(initial_board)])

    for _, move, _ in board.history:
        sgf_coord = int_to_sgf_coord(move.coord)
        if move.color == Color.BLACK:
            node = SGFNode({"B": SGFPropValues([sgf_coord])})
        else:
            node = SGFNode({"W": SGFPropValues([sgf_coord])})
        tree.append_node(node)

    with path.open("w") as f:
        f.write(str(tree))


if __name__ == "__main__":
    save_board_to_sgf(
        sgf_root_to_board(
            "tests/problems/cho-1-elementary/cho-1-elementary-900.sgf"
        ),
        Path("haha.sgf"),
    )
