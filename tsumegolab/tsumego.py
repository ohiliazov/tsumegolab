import itertools
from dataclasses import dataclass
from enum import IntEnum

import numpy as np
from scipy.ndimage import binary_dilation

from tsumegolab.utils.coord_utils import int_to_gtp_coord

# fmt: off
STRUCTURE = np.array(
    [
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1],
    ],
    dtype=np.int8,
)
OFFENCE_KO_THREAT = np.array(
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0,-1,-1,-1,-1,-1],
        [1, 0, 0, 1, 1, 1, 0,-1, 0],
    ],
    dtype=np.int8,
)
DEFENCE_KO_THREAT = np.array(
    [
        [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [ 1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
        [ 1,-1, 0, 0, 0, 1, 1, 1, 1, 1, 1,-1, 0,-1],
        [ 1,-1, 0, 0,-1,-1,-1, 0, 1, 0, 1,-1,-1, 0],
    ],
    dtype=np.int8,
)
# fmt: on


class Color(IntEnum):
    B = 1
    W = -1


@dataclass
class RotationSpec:
    flip_x: bool
    flip_y: bool
    transpose: bool


class Tsumego:
    def __init__(
        self,
        board: np.ndarray,
        ko_allowed: bool = False,
        wall_distance: int = 4,
    ):
        self.board, self.rotation_spec = self._normalize_rotation(
            board.astype(np.int8)
        )
        self.frame_color = self._frame_color()
        self.ko, self.ko_mask = self._ko_threat(ko_allowed)
        self.inside = self._inside_mask(wall_distance)
        self.outside = self._outside_mask()
        self.wall = self.inside & self.outside
        self.tsumego_frame = self._tsumego_frame()
        self.allowed_moves_mask = self._allowed_moves_mask()

    @staticmethod
    def _normalize_rotation(
        board: np.ndarray
    ) -> tuple[np.ndarray[int], RotationSpec]:
        stones_mean = np.mean(np.argwhere(board), axis=0)
        x, y = stones_mean - (np.array(board.shape) - 1) / 2

        if flip_x := x > 0:
            board = np.flip(board, axis=0)
        if flip_y := y > 0:
            board = np.flip(board, axis=1)
        if transpose := abs(x) < abs(y):
            board = np.transpose(board)

        return board, RotationSpec(flip_x, flip_y, transpose)

    def _inside_mask(self, wall_distance: int) -> np.ndarray[bool]:
        return binary_dilation(self.board, STRUCTURE, wall_distance)

    def _outside_mask(self) -> np.ndarray[bool]:
        return binary_dilation(~self.inside, STRUCTURE)

    def _ko_threat(
        self, ko_allowed: bool
    ) -> tuple[np.ndarray[np.int8], np.ndarray[bool]]:
        if ko_allowed ^ (self.frame_color == Color.B):
            ko_threat = OFFENCE_KO_THREAT
        else:
            ko_threat = DEFENCE_KO_THREAT

        height, width = self.board.shape
        ko_x, ko_y = ko_threat.shape
        ko_threat = np.pad(
            ko_threat, pad_width=((height - ko_x, 0), (width - ko_y, 0))
        )
        ko_mask = np.zeros(self.board.shape, dtype=bool)
        ko_mask[-ko_x:, -ko_y:] = True
        return ko_threat, ko_mask

    def _tsumego_frame(self) -> np.ndarray[np.int8]:
        tsumego_frame = np.copy(self.board)

        r, c = self.board.shape
        for i, j in itertools.product(range(r), range(c)):
            if self.outside[i, j] and i % 2 + j % 2 == 1:
                tsumego_frame[i, j] = self.frame_color

        tsumego_frame[self.wall] = self.frame_color

        np.putmask(tsumego_frame, self.ko_mask, self.ko * self.frame_color)

        return tsumego_frame

    def _frame_color(self) -> Color:
        bx, by = np.average(np.where(self.board == Color.B), axis=1)
        wx, wy = np.average(np.where(self.board == Color.W), axis=1)

        distance_b = bx**2 + by**2
        distance_w = wx**2 + wy**2

        return Color.B if distance_b > distance_w else Color.W

    def _allowed_moves_mask(self) -> np.ndarray[bool]:
        return np.logical_or(
            np.logical_and(self.inside, ~self.wall),
            self.ko_mask,
        )

    @property
    def initial_stones(self) -> list[tuple[str, str]]:
        stones = []
        for coord in np.argwhere(self.tsumego_frame == Color.B):
            stones.append((Color.B.name, int_to_gtp_coord(coord)))
        for coord in np.argwhere(self.tsumego_frame == Color.W):
            stones.append((Color.W.name, int_to_gtp_coord(coord)))
        return stones

    @property
    def to_kill(self) -> bool:
        return self.frame_color == Color.B
