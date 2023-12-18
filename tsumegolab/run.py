from pprint import pprint

from tsumegolab.katago import KataAnalysis
from tsumegolab.utils.kifu_utils import sgf_to_initial_stones

path = (
    "/Users/oleksandr.hiliazov/PycharmProjects/tsumegolab"
    "/tests/problems/cho-1-elementary/cho-1-elementary-1.sgf"
)

initial_stones_stones = sgf_to_initial_stones(path)

pprint(initial_stones_stones)

kata = KataAnalysis()

unexplored = [[]]

while unexplored:
    moves = unexplored.pop()
    black_response = kata.query(initial_stones_stones, moves)
    pprint(black_response["rootInfo"])
    black_best_score = black_response["rootInfo"]["scoreLead"]
    black_stdev = black_response["rootInfo"]["scoreStdev"]
    white_response = kata.query(
        initial_stones_stones, moves, initialPlayer="W"
    )
    pprint(white_response["rootInfo"])
    white_best_score = white_response["rootInfo"]["scoreLead"]

    score_threshold = (black_best_score - white_best_score) / 2
    for black_move in black_response["moveInfos"]:
        if black_best_score - black_move["scoreLead"] < score_threshold:
            print("B", black_move)
    for white_move in white_response["moveInfos"]:
        if white_best_score - white_move["scoreLead"] > -score_threshold:
            print("W", white_move)
