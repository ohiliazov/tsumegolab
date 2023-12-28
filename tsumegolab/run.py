import numpy as np

from tsumegolab.katago import Color, KataAnalysis, PresetRules, QueryData
from tsumegolab.utils.kifu_utils import sgf_to_initial_stones_and_allowed_moves

path = (
    "/Users/oleksandr.hiliazov/PycharmProjects/tsumegolab"
    "/tests/problems/cho-1-elementary/cho-1-elementary-11.sgf"
)

(
    initial_stones_stones,
    allowed_mask,
    outside_color,
) = sgf_to_initial_stones_and_allowed_moves(path)

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
    print(np.all(black_ownership[allowed_mask] == outside_color))

kata.engine.kill()
