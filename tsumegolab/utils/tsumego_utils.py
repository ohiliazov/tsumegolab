import itertools

import numpy as np
from scipy.ndimage import binary_dilation

from tsumegolab.utils.board_utils import normalize_rotation, rotate_board

edge_structure = np.ones((3, 3))

# fmt: off
inside_ko_threat = np.array(
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0,-1,-1,-1,-1,-1],
        [1, 0, 0, 1, 1, 1, 0,-1, 0],
    ]
)
outside_ko_threat = np.array(
    [
        [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [ 1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
        [ 1,-1, 0, 0, 0, 1, 1, 1, 1, 1, 1,-1, 0,-1],
        [ 1,-1, 0, 0,-1,-1,-1, 0, 1, 0, 1,-1,-1, 0],
    ]
)
# fmt: on


def get_inside_mask(board, distance: int) -> np.ndarray:
    return binary_dilation(
        board,
        structure=edge_structure,
        iterations=distance,
    )


def get_outside_mask(inside_mask: np.ndarray) -> np.ndarray:
    return binary_dilation(~inside_mask, structure=edge_structure)


def tsumego_frame_mask(
    inside_mask: np.ndarray, outside_mask: np.ndarray
) -> np.ndarray:
    outside = np.copy(outside_mask)

    r, c = inside_mask.shape
    for i, j in itertools.product(range(r), range(c)):
        outside[i, j] = outside[i, j] and i % 2 + j % 2 == 1

    outside[inside_mask & outside_mask] = True
    return outside


def count_stones_by_axis(board: np.ndarray, axis: int) -> int:
    return np.take_along_axis(
        board,
        np.argmax(board != 0, axis=axis, keepdims=True),
        axis=axis,
    ).sum()


def guess_outside_color(board: np.ndarray):
    bx, by = np.average(np.where(board == 1), axis=1)
    wx, wy = np.average(np.where(board == -1), axis=1)

    if bx**2 + by**2 > wx**2 + wy**2:
        return 1
    return -1


def tsumego_frame(
    board: np.ndarray,
    distance: int = 4,
    ko_allowed: bool = False,
) -> tuple[np.ndarray, np.ndarray, int]:
    board, rotation_spec = normalize_rotation(board)

    inside_mask = get_inside_mask(board, distance)
    outside_mask = get_outside_mask(inside_mask)
    mask = tsumego_frame_mask(inside_mask, outside_mask)
    outside_color = guess_outside_color(board)

    board[mask] = outside_color
    ko_threat = inside_ko_threat if ko_allowed else outside_ko_threat
    ko_x, ko_y = ko_threat.shape
    board[-ko_x:, -ko_y:] = ko_threat * outside_color
    return rotate_board(board, rotation_spec), rotate_board(
        inside_mask, rotation_spec
    ), outside_color
