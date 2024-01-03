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
ONE_KO_THREAT_DEFENCE = np.array(
    [
        [1, 1, 1, 1, 1],
        [1,-1,-1,-1,-1],
        [1, 0, 0, 0, 0],
    ],
    dtype=np.int8,
)
ONE_KO_THREAT_OFFENCE = np.array(
    [
        [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [ 1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
        [ 1,-1, 1, 1, 1, 1, 1,-1, 0,-1],
        [ 1,-1, 0, 0, 0, 0, 1,-1,-1, 0],
    ],
    dtype=np.int8,
)
KO_THREAT_DEFENCE = np.array(
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0,-1,-1,-1,-1,-1],
        [1, 0, 0, 1, 1, 1, 0,-1, 0],
    ],
    dtype=np.int8,
)
KO_THREAT_OFFENCE = np.array(
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
        ko_allowed: bool,
        wall_distance: int,
        ownership_threshold: float,
    ):
        self.ko_allowed = ko_allowed
        self.ownership_threshold = ownership_threshold
        self.board, self.rotation_spec = self._normalize_rotation(
            board.astype(np.int8)
        )
        self.frame_color = self._frame_color()
        self.ko, self.ko_put_mask, self.ko_check_mask = self._ko_threat()
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
        self
    ) -> tuple[np.ndarray[np.int8], np.ndarray[bool], np.ndarray[bool]]:
        ko = np.zeros(self.board.shape, dtype=np.int8)

        if self.ko_allowed ^ self.to_kill:
            # to kill and ko not allowed OR to live and ko is allowed
            ko_threat = KO_THREAT_DEFENCE
        else:
            # to kill and ko is allowed OR to live and ko not allowed
            ko_threat = KO_THREAT_OFFENCE

        ko_x, ko_y = ko_threat.shape
        ko[-ko_x:, -ko_y:] = ko_threat

        ko_put_mask = np.zeros(self.board.shape, dtype=bool)
        ko_put_mask[-ko_x:, -ko_y:] = True

        if self.ko_allowed ^ self.to_kill:
            ko_check_mask = ko_put_mask.copy()
        else:
            ko_check_mask = np.zeros(self.board.shape, dtype=bool)
            ko_check_mask[-ko_x + 1 :, -ko_y + 1 :] = True
        return ko, ko_put_mask, ko_check_mask

    def _tsumego_frame(self) -> np.ndarray[np.int8]:
        tsumego_frame = self.board.astype(np.int8)

        r, c = self.board.shape
        for i, j in itertools.product(range(r), range(c)):
            if self.outside[i, j] and i % 2 + j % 2 == 1:
                tsumego_frame[i, j] = self.frame_color

        tsumego_frame[self.wall] = self.frame_color

        np.putmask(tsumego_frame, self.ko_put_mask, self.ko * self.frame_color)

        return tsumego_frame

    def _take_along_by_axis(self, axis: int) -> int:
        return np.take_along_axis(
            np.flip(self.board),
            np.argmax(np.flip(self.board) != 0, axis=axis, keepdims=True),
            axis=axis,
        ).sum()

    def _frame_color(self) -> Color:
        colors_sum = self._take_along_by_axis(axis=0)
        colors_sum += self._take_along_by_axis(axis=1)
        return Color.B if colors_sum > 0 else Color.W

    def _allowed_moves_mask(self) -> np.ndarray[bool]:
        return np.logical_or(
            np.logical_and(self.inside, ~self.wall),
            self.ko_put_mask,
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

    def is_owned_by(
        self,
        ownership: np.ndarray[float],
        mask: np.ndarray[bool],
        color: Color,
    ):
        if color == Color.B:
            return np.all(ownership[mask] > self.ownership_threshold)
        return np.all(ownership[mask] < -self.ownership_threshold)

    def is_correct(self, ownership: np.ndarray) -> bool:
        group_all_black = self.is_owned_by(ownership, self.inside, Color.B)
        group_all_white = self.is_owned_by(ownership, self.inside, Color.W)
        ko_all_black = self.is_owned_by(ownership, self.ko_check_mask, Color.B)
        ko_all_white = self.is_owned_by(ownership, self.ko_check_mask, Color.W)

        if self.to_kill:
            if self.ko_allowed:
                return group_all_black or not ko_all_white
            else:
                return group_all_black and ko_all_black
        else:
            if self.ko_allowed:
                return not group_all_white or ko_all_black
            else:
                return not group_all_white and not ko_all_white

    def print_frame(self):
        for row in self.tsumego_frame:
            for cell in row:
                if cell == Color.B:
                    print("B", end="")
                elif cell == Color.W:
                    print("W", end="")
                else:
                    print(".", end="")
            print()

    def print_ownership(self, ownership: np.ndarray):
        print(ownership)
        for row in ownership:
            for cell in row:
                if cell > 0.7:
                    print("B", end="")
                elif cell < -0.7:
                    print("W", end="")
                else:
                    print(".", end="")
            print()
