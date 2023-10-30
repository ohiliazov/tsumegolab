from pathlib import Path

import numpy as np

from .board import Board, Color
from .sgftree import SGFNode, SGFParser, SGFPropValues, SGFTree

SGF_COORDINATES = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def sgf_coord_to_int(coord: str) -> tuple:
    x = SGF_COORDINATES.index(coord[0])
    y = SGF_COORDINATES.index(coord[1])
    return y, x


def int_coord_to_sgf(coord: tuple) -> str:
    x = SGF_COORDINATES[coord[0]]
    y = SGF_COORDINATES[coord[1]]
    return f"{y}{x}"


def get_initial_board_from_sgf(path: Path | str):
    parser = SGFParser.parse_file(Path(path))

    root_node = parser.parse()[0][0]

    sz = root_node.get_prop_value("SZ")
    if ":" in sz:
        width, height = sz.split(":")
    else:
        width = height = sz[0]
    shape = int(width), int(height)

    black = root_node.get_prop_value("AB")
    white = root_node.get_prop_value("AW")

    array = np.zeros(shape)

    for sgf_coord in black:
        array[sgf_coord_to_int(sgf_coord)] = Color.BLACK

    for sgf_coord in white:
        array[sgf_coord_to_int(sgf_coord)] = Color.WHITE

    return Board(array)


def stones_to_sgf(size: int, black: list[str], white: list[str]) -> str:
    return str(
        SGFTree(
            [
                SGFNode(
                    {
                        "FF": SGFPropValues(["4"]),
                        "CA": SGFPropValues(["UTF-8"]),
                        "GM": SGFPropValues(["1"]),
                        "SZ": SGFPropValues([size]),
                        "AP": SGFPropValues(["tsumegolab:0.1.0"]),
                        "AB": SGFPropValues(black),
                        "AW": SGFPropValues(white),
                    }
                )
            ]
        )
    )
