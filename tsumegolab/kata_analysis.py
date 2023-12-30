import uuid
from enum import StrEnum
from pathlib import Path
from subprocess import PIPE, Popen
from threading import Thread
from typing import Any

from loguru import logger
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    ValidationError,
    confloat,
    constr,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_incrementing,
)

from tsumegolab.config import KataConfig

CONFIG_PATH = Path(__file__).parent.parent / "config" / "katago_analysis.cfg"
logger.add("katago.log", level="DEBUG")


class Color(StrEnum):
    BLACK = "B"
    WHITE = "W"


GTPLocation = constr(pattern=r"^(([A-Z]{1,2}[1-9]\d?)|pass)$")
ClosedIntervalValue = confloat(ge=-1, le=1)
NormalizedValue = confloat(ge=0, le=1)
Stone = tuple[Color, GTPLocation]


def to_camel_case(snake_case: str) -> str:
    first, *rest = snake_case.split("_")
    return first + "".join(map(str.capitalize, rest))


class CamelCaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case)


class KoRule(StrEnum):
    SIMPLE = "SIMPLE"
    POSITIONAL = "POSITIONAL"
    SITUATIONAL = "SITUATIONAL"


class ScoringRule(StrEnum):
    AREA = "AREA"
    TERRITORY = "TERRITORY"


class TaxRule(StrEnum):
    NONE = "NONE"
    SEKI = "SEKI"
    ALL = "ALL"


class WhiteHandicapBonus(StrEnum):
    ZERO = "0"
    N_MINUS_ONE = "N-1"
    N = "N"


class Rules(CamelCaseModel):
    ko: KoRule
    scoring: ScoringRule
    tax: TaxRule
    suicide: bool
    has_button: bool
    white_handicap_bonus: WhiteHandicapBonus
    friendly_pass_ok: bool


class PresetRules(StrEnum):
    TROMP_TAYLOR = "tromp-taylor"
    CHINESE = "chinese"
    CHINESE_OGS = "chinese-ogs"
    CHINESE_KGS = "chinese-kgs"
    JAPANESE = "japanese"
    KOREAN = "korean"
    STONE_SCORING = "stone-scoring"
    AGA = "aga"
    BGA = "bga"
    NEW_ZEALAND = "new-zealand"
    AGA_BUTTON = "aga-button"


class MovesDict(CamelCaseModel):
    player: Color
    moves: list[GTPLocation]
    until_depth: PositiveInt


class KataRequest(CamelCaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    moves: list[Stone]
    initial_stones: list[Stone] | None = None
    initial_player: Color | None = None
    rules: PresetRules | Rules
    komi: float | None = None
    white_handicap_bonus: WhiteHandicapBonus | None = None
    board_x_size: int
    board_y_size: int
    analyze_turns: list[int] | None = None
    max_visits: int | None = None
    root_policy_temperature: float | None = None
    root_fpu_reduction_max: float | None = None
    analysis_p_v_len: int | None = None
    include_ownership: bool | None = None
    include_ownership_stdev: bool | None = None
    include_moves_ownership: bool | None = None
    include_moves_ownership_stdev: bool | None = None
    include_policy: bool | None = None
    include_p_v_visits: bool | None = None
    avoid_moves: list[MovesDict] | None = None
    allow_moves: list[MovesDict] | None = None
    override_settings: dict[str, Any] | None = None
    report_during_search_every: float | None = None
    priority: int | None = None
    priorities: list[int] | None = None


class MoveInfo(CamelCaseModel):
    move: GTPLocation
    visits: int
    winrate: float
    score_mean: float
    score_stdev: float
    score_lead: float
    score_selfplay: float
    prior: float
    utility: float
    lcb: float
    utility_lcb: float
    weight: float
    order: int
    is_symmetry_of: GTPLocation | None = None
    pv: list[GTPLocation]
    pv_visits: int | None = None
    pv_edge_visits: int | None = None
    ownership: list[ClosedIntervalValue] | None = None
    ownership_stdev: list[NormalizedValue] | None = None


class RootInfo(CamelCaseModel):
    winrate: float
    score_lead: float
    score_selfplay: float
    utility: float
    visits: int
    this_hash: str
    sym_hash: str
    current_player: Color
    raw_st_wr_error: float
    raw_st_score_error: float
    raw_var_time_left: float


class KataResponse(CamelCaseModel):
    id: uuid.UUID
    is_during_search: bool
    turn_number: int
    move_infos: list[MoveInfo]
    rootInfo: RootInfo
    ownership: list[ClosedIntervalValue] | None = None
    ownership_stdev: list[NormalizedValue] | None = None
    policy: list[NormalizedValue] | None = None


class KataErrorResponse(CamelCaseModel):
    id: str | None = None
    error: str | None = None
    warning: str | None = None
    field: str | None = None


class KataAnalysis:
    def __init__(self, config: KataConfig):
        self.output_path = config.output_path

        cmd = [
            str(config.engine_path),
            "analysis",
            "-config",
            str(config.config_path),
        ]

        logger.info("Starting katago engine...")
        logger.info(" ".join(cmd))
        self.engine = Popen(
            args=cmd,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            text=True,
        )

        self._stdout_thread = Thread(target=self.collect_results)
        self._stdout_thread.start()

    def collect_results(self):
        while self.engine.poll() is None:
            line = self.engine.stdout.readline().strip()
            logger.info(f"RES> {line}")

            try:
                response = KataResponse.model_validate_json(line)
            except ValidationError:
                response = KataErrorResponse.model_validate_json(line)

            response_path = self.output_path / f"{response.id}.json"

            with response_path.open("w") as file:
                file.write(response.model_dump_json(by_alias=True, indent=2))

    def send_request(self, request: KataRequest):
        logger.info(f"REQ> {request}")

        query = request.model_dump_json(by_alias=True, exclude_none=True)

        self.engine.stdin.write(f"{query}\n")
        self.engine.stdin.flush()

    @retry(
        retry=retry_if_exception_type(FileNotFoundError),
        wait=wait_incrementing(1, 0.5, 5),
        stop=stop_after_attempt(100),
    )
    def get(self, request_id: uuid.UUID) -> KataResponse:
        response_path = self.output_path / f"{request_id}.json"

        with response_path.open() as file:
            return KataResponse.model_validate_json(file.read())
