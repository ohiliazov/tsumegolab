from collections import defaultdict
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterator

import numpy as np

Coord = tuple[int, int]


class InvalidMove(Exception):
    pass


class Color(IntEnum):
    BLACK = 1
    EMPTY = 0
    WHITE = -1


@dataclass
class Move:
    color: Color
    coord: Coord


class Board:
    def __init__(
        self,
        board_or_shape: tuple[int, int] | np.ndarray,
        turn: Color = Color.BLACK,
        suicide_allowed: bool = False,
    ):
        if isinstance(board_or_shape, tuple):
            self.board = np.zeros(board_or_shape, dtype=np.int8)
        else:
            self.board = board_or_shape

        self.turn = turn
        self.suicide_allowed = suicide_allowed

        self.score: dict[Color, int] = defaultdict(int)
        self.history: list[tuple[np.ndarray, Move, dict[Color, int]]] = []

    @property
    def shape(self):
        return self.board.shape

    @property
    def width(self):
        return self.shape[0]

    @property
    def height(self):
        return self.shape[1]

    def _is_valid_coord(self, coord: Coord) -> bool:
        x, y = coord
        return 0 <= x < self.width and 0 <= y < self.height

    def _get_color(self, coord: Coord) -> Color:
        if self._is_valid_coord(coord):
            return Color(self.board[coord])

        raise InvalidMove("invalid point")

    def _iter_adjacent(self, coord: Coord) -> Iterator[Coord]:
        x, y = coord
        if x > 0:
            yield x - 1, y
        if x < self.width - 1:
            yield x + 1, y
        if y > 0:
            yield x, y - 1
        if y < self.height - 1:
            yield x, y + 1

    def _get_group(self, coord: Coord) -> set[Coord]:
        color = self._get_color(coord)

        to_expand = {coord}
        group = set()

        while to_expand:
            coord = to_expand.pop()
            to_expand |= {
                adj_coord
                for adj_coord in self._iter_adjacent(coord)
                if self._get_color(*adj_coord) == color
            }

            group.add(coord)
            to_expand -= group

        return group

    def _push_history(self, move: Move):
        self.history.append((np.copy(self.board), move, self.score))

    def _pop_history(self):
        self.board, move, self.score = self.history.pop()
        self.turn = move.color

    def _place_stone(self, coord: Coord):
        if self._get_color(coord) != Color.EMPTY:
            raise InvalidMove("point not empty")

        self.board[coord] = self.turn

    def _kill_group(self, group: set[Coord]):
        self.board[tuple(zip(*group))] = Color.EMPTY

    def _liberties(self, group: set[Coord]) -> set[Coord]:
        return {
            crd
            for coord in group
            for crd in self._iter_adjacent(coord)
            if self._get_color(crd) == Color.EMPTY
        }

    def _process_killing(self, coord: Coord):
        group = self._get_group(coord)
        if not self._liberties(group):
            self._kill_group(group)
            self.score[self.turn] += len(group)

    def _process_capture(self, coord: Coord):
        for coord in self._iter_adjacent(coord):
            if self._get_color(*coord) == -self.turn:
                self._process_killing(*coord)

    def _process_suicide(self, coord: Coord):
        group = self._get_group(coord)

        if not self._liberties(group):
            if len(group) == 1 or not self.suicide_allowed:
                raise InvalidMove("suicide move")

            self._kill_group(group)
            self.score[-self.turn] += len(group)

    def _process_ko(self):
        if len(self.history) > 1:
            prev_board, *_ = self.history[-2]
            if np.array_equal(self.board, prev_board):
                raise InvalidMove("ko violation")

    def _move(self, coord: Coord):
        self._place_stone(coord)
        self._process_capture(coord)
        self._process_suicide(coord)
        self._process_ko()

        self.turn = -self.turn

    def move(self, x: int, y: int):
        coord = x, y
        move = Move(self.turn, coord)
        self._push_history(move)
        try:
            self._move(coord)
        except InvalidMove:
            self._pop_history()
