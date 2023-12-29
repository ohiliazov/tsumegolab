import numpy as np

from tsumegolab.katago import Color, KataAnalysis, PresetRules, QueryData
from tsumegolab.tsumego import Tsumego
from tsumegolab.utils.kifu_utils import sgf_root_to_board

path = (
    "/Users/oleksandr.hiliazov/PycharmProjects/tsumegolab"
    "/tests/problems/cho-1-elementary/cho-1-elementary-11.sgf"
)

board = sgf_root_to_board(path)
tsumego = Tsumego(board, ko_allowed=True)
initial_stones_stones = tsumego.stones
allowed_mask = tsumego.allowed_moves_mask

kata = KataAnalysis()

unexplored = [[]]

while unexplored:
    moves = unexplored.pop()
    query_as_black = QueryData.model_construct(
        initial_player=Color.BLACK,
        initial_stones=initial_stones_stones,
        moves=moves,
        rules=PresetRules.JAPANESE,
        board_x_size=19,
        board_y_size=19,
        include_ownership=True,
        max_visits=2500,
        # include_moves_ownership=True,
    )
    query_as_white = QueryData.model_construct(
        initial_player=Color.WHITE,
        initial_stones=initial_stones_stones,
        moves=moves,
        rules=PresetRules.JAPANESE,
        board_x_size=19,
        board_y_size=19,
        include_ownership=True,
        # include_moves_ownership=True,
    )

    kata.query(query_as_black)
    kata.query(query_as_white)
    black_response = kata.get(query_as_black.id)
    white_response = kata.get(query_as_white.id)

    black_ownership = np.reshape(
        np.round(black_response.ownership), allowed_mask.shape
    )
    white_ownership = np.reshape(
        np.round(white_response.ownership), allowed_mask.shape
    )

    print(black_ownership)
    print(allowed_mask)
    print(np.all(black_ownership[allowed_mask] == tsumego.frame_color))

kata.engine.kill()
