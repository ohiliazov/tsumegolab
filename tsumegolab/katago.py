import json
import uuid
from pathlib import Path
from subprocess import PIPE, Popen

CONFIG_PATH = Path(__file__).parent.parent / "config" / "katago_analysis.cfg"


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

    def _query_raw(self, data: dict) -> dict:
        self.engine.stdin.write(json.dumps(data) + "\n")
        self.engine.stdin.flush()

        line = ""
        while not line:
            if exit_code := self.engine.poll():
                raise Exception(f"katago exited with code {exit_code}")
            line = self.engine.stdout.readline().strip()

        return json.loads(line)

    def query(
        self,
        initial_stones: list[tuple[str, str]],
        moves: list[tuple[str, str]],
        rules: str = "japanese",
        komi: float = 0,
        board_x_size: int = 19,
        board_y_size: int = 19,
        **kwargs,
    ) -> dict:
        query_id = str(uuid.uuid4())
        data = {
            "id": query_id,
            "initialStones": initial_stones,
            "moves": moves,
            "rules": rules,
            "komi": komi,
            "boardXSize": board_x_size,
            "boardYSize": board_y_size,
            "analyzeTurns": [len(moves)],
            **kwargs,
        }
        return self._query_raw(data)
