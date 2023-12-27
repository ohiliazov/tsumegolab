from tsumegolab.katago import KataAnalysis, PresetRules, QueryData
from tsumegolab.utils.kifu_utils import sgf_to_initial_stones_and_allowed_moves

path = (
    "/Users/oleksandr.hiliazov/PycharmProjects/tsumegolab"
    "/tests/problems/cho-1-elementary/cho-1-elementary-1.sgf"
)

(
    initial_stones_stones,
    allowed_mask,
    color,
) = sgf_to_initial_stones_and_allowed_moves(path)

kata = KataAnalysis()

unexplored = [[]]

while unexplored:
    moves = unexplored.pop()
    query = QueryData.model_construct(
        initial_stones=initial_stones_stones,
        moves=moves,
        rules=PresetRules.JAPANESE,
        board_x_size=19,
        board_y_size=19,
        include_ownership=True,
        include_moves_ownership=True,
    )

    kata.query(query)
    black_response = kata.get(query.id)

kata.engine.kill()
