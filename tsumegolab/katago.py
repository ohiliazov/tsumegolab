import uuid
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, constr

CONFIG_PATH = Path(__file__).parent.parent / "config" / "katago_analysis.cfg"

Color = Literal["B", "W"]
GTPCoord = constr(pattern=r"[A-Z]{1,2}[1-9]\d?")
Stone = tuple[Color, GTPCoord]


def to_camel_case(snake_case: str) -> str:
    first, *rest = snake_case.split("_")
    return first + "".join(map(str.capitalize, rest))


class CamelcaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case)


class QueryData(CamelcaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    initial_stones: list[Stone] = Field(default_factory=list)
    moves: list[Stone] = Field(default_factory=list)
    rules: str = "japanese"
    komi: float = 0.0
    board_x_size: int = 19
    board_y_size: int = 19
    analyze_turns: list[int] = Field(default_factory=lambda: [0])


class MoveInfo(CamelcaseModel):
    lcb: float
    move: GTPCoord
    order: int
    prior: float
    pv: list[GTPCoord]
    score_lead: float
    score_mean: float
    score_selfplay: float
    score_stdev: float
    utility: float
    utility_lcb: float
    visits: int
    weight: float
    winrate: float
    is_symmetry_of: GTPCoord | None = None


class RootInfo(CamelcaseModel):
    current_player: Color
    raw_st_score_error: float
    raw_st_wr_error: float
    raw_var_time_left: float
    score_lead: float
    score_selfplay: float
    score_stdev: float
    sym_hash: str
    this_hash: str
    visits: int
    weight: float
    winrate: float


class KataResponse(CamelcaseModel):
    id: uuid.UUID
    is_during_search: bool
    move_infos: list[MoveInfo]
    rootInfo: RootInfo
    turn_number: int


class KataAnalysis:
    def __init__(
        self,
        engine_path: str = "katago",
        config_path: Path | str = CONFIG_PATH,
        model_path: str | None = None,
    ):
        cmd = [engine_path, "analysis", "-config", str(config_path)]

        if model_path:
            cmd.extend(["-model", model_path])

        self.engine = Popen(
            args=cmd,
            stdin=PIPE,
            stdout=PIPE,
            text=True,
        )

    def query(self, query: QueryData) -> KataResponse:
        self.engine.stdin.write(query.model_dump_json(by_alias=True))
        self.engine.stdin.write("\n")
        self.engine.stdin.flush()

        line = ""
        while not line:
            if exit_code := self.engine.poll():
                raise Exception(f"katago exited with code {exit_code}")
            line = self.engine.stdout.readline().strip()

        return KataResponse.model_validate_json(line)
