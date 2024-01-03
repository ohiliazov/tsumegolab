import itertools
import json
from pathlib import Path

import numpy as np
from loguru import logger

from tsumegolab.config import Settings
from tsumegolab.kata_analysis import KataAnalysis, KataRequest, PresetRules
from tsumegolab.tsumego import Color, Tsumego
from tsumegolab.utils.kifu_utils import sgf_root_to_board

kata_config = Settings()
kata = KataAnalysis(kata_config)

problems = Path(
    "/Users/oleksandr.hiliazov/PycharmProjects/tsumegolab"
    "/tests/problems/cho-1-elementary"
)


def send_and_get_correctness(
    path: Path, board: np.ndarray, ko_allowed: bool, visits: int
):
    tsumego = Tsumego(
        board,
        ko_allowed=ko_allowed,
        wall_distance=kata_config.wall_distance,
        ownership_threshold=kata_config.ownership_threshold,
    )
    query = KataRequest.model_construct(
        id=f"{path.name}-{visits}",
        initial_player=Color.B.name,
        initial_stones=tsumego.initial_stones,
        moves=[],
        rules=PresetRules.JAPANESE,
        board_x_size=19,
        board_y_size=19,
        include_ownership=True,
        max_visits=visits,
    )

    kata.send_request(query)
    response = kata.get(query.id)

    ownership = np.reshape(response.ownership, board.shape)

    return tsumego.is_correct(ownership), tsumego.to_kill


VISITS = [100, 200, 500, 1000]

visits_data = {}
for max_visits in VISITS:
    try:
        with open(f"data-{max_visits}-visits.json") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {
            "to_live": [],
            "to_kill": [],
            "to_live_ko": [],
            "to_kill_ko": [],
            "unsolved": [],
        }
    visits_data[max_visits] = data


for idx, path in enumerate(sorted(problems.iterdir())):
    for max_visits in VISITS:
        data = visits_data[max_visits]

        solved = set(itertools.chain(*data.values()))

        if path.name in solved:
            logger.info(f"Skipping problem {idx+1} with {max_visits} visits.")
            continue

        board = sgf_root_to_board(path)
        is_correct, to_kill = send_and_get_correctness(
            path, board, ko_allowed=False, visits=max_visits
        )
        if is_correct:
            if to_kill:
                data["to_kill"].append(path.name)
            else:
                data["to_live"].append(path.name)
            logger.info(f"NO KO {to_kill=} {path.name}")
        else:
            is_correct = send_and_get_correctness(
                path, board, ko_allowed=True, visits=max_visits
            )
            if is_correct:
                if to_kill:
                    data["to_kill_ko"].append(path.name)
                else:
                    data["to_live_ko"].append(path.name)
                logger.info(f"ONLY KO {to_kill=} {path.name}")
            else:
                data["unsolved"].append(path.name)
                logger.info(f"UNSOLVED {to_kill=} {path.name}")

        with open(f"data-{max_visits}-visits.json", "w") as file:
            json.dump(data, file, indent=2)

kata.engine.kill()
