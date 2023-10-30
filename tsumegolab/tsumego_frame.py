import itertools

import numpy as np
from scipy.ndimage import binary_dilation

from tsumegolab.utils import int_coord_to_sgf, stones_to_sgf

edge_structure = np.ones((3, 3))


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


def tsumego_frame(board: np.ndarray, distance: int) -> np.ndarray:
    mask = tsumego_frame_mask(board, distance)
    board[mask] = guess_outside_color(board, distance)
    return board


def _take_along_axis_sum(board: np.ndarray, flip: bool, axis: int) -> int:
    if flip:
        board = np.flip(board)

    return np.take_along_axis(
        board,
        np.argmax(board != 0, axis=axis, keepdims=True),
        axis=axis,
    ).sum()


def guess_outside_color(board: np.ndarray, distance: int):
    outside = get_outside_mask(board, distance)

    colors_sum = 0

    if outside[0].all():
        colors_sum += _take_along_axis_sum(board, flip=True, axis=0)

    if outside[:, 0].all():
        colors_sum += _take_along_axis_sum(board, flip=True, axis=1)

    if outside[-1].all():
        colors_sum += _take_along_axis_sum(board, flip=False, axis=0)

    if outside[:, -1].all():
        colors_sum += _take_along_axis_sum(board, flip=False, axis=1)

    if colors_sum > 0:
        return 1
    if colors_sum < 0:
        return -1
    return 0


if __name__ == "__main__":
    tsumego_array = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, -1, -1, -1, -1, -1, -1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, -1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, -1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
    )

    frame = tsumego_frame(tsumego_array, distance=5)

    AB = []
    AW = []

    for i, j in itertools.product(range(19), range(19)):
        coord = int_coord_to_sgf((j, i))

        if frame[i, j] == 1:
            AB.append(coord)
        if frame[i, j] == -1:
            AW.append(coord)
    print(stones_to_sgf(tsumego_array.shape[0], AB, AW))
    for row in frame:
        for s in row:
            print("B" if s == 1 else "W" if s == -1 else ".", end=" ")
        print()
