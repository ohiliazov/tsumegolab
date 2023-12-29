import numpy as np

from tsumegolab.kata_analysis import KataAnalysis, KataRequest, PresetRules
from tsumegolab.tsumego import Color, Tsumego
from tsumegolab.utils.kifu_utils import sgf_root_to_board

path = (
    "/Users/oleksandr.hiliazov/PycharmProjects/tsumegolab"
    "/tests/problems/cho-1-elementary/cho-1-elementary-11.sgf"
)

board = sgf_root_to_board(path)
tsumego = Tsumego(board, ko_allowed=True)
allowed_mask = tsumego.allowed_moves_mask

if tsumego.frame_color:
    pass


kata = KataAnalysis()

unexplored = [[]]

while unexplored:
    moves = unexplored.pop()
    query_as_black = KataRequest.model_construct(
        initial_player=Color.B.name,
        initial_stones=tsumego.initial_stones,
        moves=moves,
        rules=PresetRules.JAPANESE,
        board_x_size=19,
        board_y_size=19,
        include_ownership=True,
        max_visits=2500,
        # include_moves_ownership=True,
    )
    query_as_white = KataRequest.model_construct(
        initial_player=Color.W.name,
        initial_stones=tsumego.initial_stones,
        moves=moves,
        rules=PresetRules.JAPANESE,
        board_x_size=19,
        board_y_size=19,
        include_ownership=True,
        # include_moves_ownership=True,
    )

    kata.send_request(query_as_black)
    kata.send_request(query_as_white)
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
