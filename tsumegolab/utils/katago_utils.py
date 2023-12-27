import numpy as np

from tsumegolab.katago import Color, MovesDict
from tsumegolab.utils.coord_utils import int_to_gtp_coord


def mask_to_moves_dict(mask: np.ndarray) -> list[MovesDict]:
    return [
        MovesDict.model_construct(
            player=color,
            moves=list(map(int_to_gtp_coord, np.argwhere(mask))),
            until_depth=300,
        )
        for color in Color
    ]
