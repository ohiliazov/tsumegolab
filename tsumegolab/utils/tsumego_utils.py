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


def get_outside_mask(board: np.ndarray, distance: int) -> np.ndarray:
    not_inside_mask = ~get_inside_mask(board, distance)
    return binary_dilation(not_inside_mask, structure=edge_structure)


def get_wall_mask(board: np.ndarray, distance: int) -> np.ndarray:
    inside_mask = get_inside_mask(board, distance)
    outside_mask = get_outside_mask(board, distance)

    return inside_mask & outside_mask


def tsumego_frame_mask(board: np.ndarray, distance: int) -> np.ndarray:
    outside = get_outside_mask(board, distance)
    wall = get_wall_mask(board, distance)

    r, c = board.shape
    for i, j in itertools.product(range(r), range(c)):
        outside[i, j] = outside[i, j] and i % 2 + j % 2 == 1

    outside[wall] = True
    return outside


def count_stones_by_axis(board: np.ndarray, axis: int) -> int:
    return np.take_along_axis(
        board,
        np.argmax(board != 0, axis=axis, keepdims=True),
        axis=axis,
    ).sum()


def guess_outside_color(board: np.ndarray, distance: int):
    outside_mask = get_outside_mask(board, distance)

    colors_sum = 0

    if outside_mask[0].all():
        colors_sum += count_stones_by_axis(np.flip(board), axis=0)
    if outside_mask[:, 0].all():
        colors_sum += count_stones_by_axis(np.flip(board), axis=1)
    if outside_mask[-1].all():
        colors_sum += count_stones_by_axis(board, axis=0)
    if outside_mask[:, -1].all():
        colors_sum += count_stones_by_axis(board, axis=1)

    return max(-1, min(1, colors_sum))


def tsumego_frame(
    board: np.ndarray,
    distance: int = 4,
    ko_allowed: bool = False,
) -> np.ndarray:
    board, rotation_spec = normalize_rotation(board)

    mask = tsumego_frame_mask(board, distance)
    outside_color = guess_outside_color(board, distance)
    board[mask] = outside_color

    ko_threat = inside_ko_threat if ko_allowed else outside_ko_threat
    ko_x, ko_y = ko_threat.shape
    board[-ko_x:, -ko_y:] = ko_threat * outside_color

    return rotate_board(board, rotation_spec)
