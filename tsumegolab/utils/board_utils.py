import numpy as np

RotationSpec = tuple[bool, bool, bool]


def normalize_rotation(board: np.ndarray) -> tuple[np.ndarray, RotationSpec]:
    stones_mean = np.mean(np.argwhere(board), axis=0)
    x, y = stones_mean - (np.array(board.shape) - 1) / 2

    if flip_x := x > 0:
        board = np.flip(board, axis=0)
    if flip_y := y > 0:
        board = np.flip(board, axis=1)
    if transpose := abs(x) < abs(y):
        board = np.transpose(board)

    return board, (flip_x, flip_y, transpose)


def rotate_board(board: np.ndarray, spec: RotationSpec) -> np.ndarray:
    flip_x, flip_y, transpose = spec

    if transpose:
        board = np.transpose(board)
    if flip_y:
        board = np.flip(board, axis=1)
    if flip_x:
        board = np.flip(board, axis=0)

    return board
