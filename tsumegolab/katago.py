import os
import re
import time
from pprint import pprint
from subprocess import PIPE, Popen
from typing import IO

MOVE_REGEX = re.compile(r"move ([A-Z]{1,2}[0-9]{1,2}|pass)")
SCORE_LEAD_REGEX = re.compile(r"scoreLead (-?[0-9.]+)")


def parse_info(line: str) -> list[dict]:
    moves_info = []
    start_idx = 0
    best_score = float("-inf")
    while start_idx is not None:
        end_idx = line.find("info", start_idx + 1)
        if end_idx == -1:
            end_idx = None

        info_line = line[start_idx:end_idx]
        try:
            move = MOVE_REGEX.search(info_line).group(1)
            score = float(SCORE_LEAD_REGEX.search(info_line).group(1))
        except AttributeError:
            print(info_line)
            raise

        score = round(score * 2) / 2
        best_score = max(best_score, score)

        moves_info.append(
            {
                "move": move,
                "score": score,
            }
        )

        start_idx = end_idx

    for move in moves_info:
        move["score"] = move["score"] - best_score

    return sorted(
        filter(lambda x: x["score"] > -15, moves_info),
        key=lambda x: -x["score"],
    )


class KataGo:
    def __init__(self):
        self.gtp = Popen(
            ["katago", "gtp", "-config", "config/katago_gtp.cfg"],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            text=True,
        )

    @staticmethod
    def _non_blocking_read(fd: IO[str]) -> list[str]:
        is_blocking = os.get_blocking(fd.fileno())
        os.set_blocking(fd.fileno(), False)
        lines = fd.readlines()
        os.set_blocking(fd.fileno(), is_blocking)
        return lines

    def _drain(self) -> tuple[list[str], list[str]]:
        stdout = self._non_blocking_read(self.gtp.stdout)
        stderr = self._non_blocking_read(self.gtp.stderr)
        return stdout, stderr

    def _read_stdout(self):
        return self.gtp.stdout.readline()

    def _send_command(self, text: str) -> str:
        self.gtp.stdin.write(text.strip() + "\n")
        self.gtp.stdin.flush()
        return self._read_stdout()

    def load_sgf(self, path: str) -> str:
        return self._send_command(f"loadsgf {path}")

    def analyze(self, seconds: int = 20) -> list[dict]:
        self._drain()

        self._send_command("kata-analyze white 100")

        end_time = time.time() + seconds

        analysis = None
        while time.time() < end_time:
            analysis = self._read_stdout()
            pprint(parse_info(analysis))

        if analysis is None:
            raise Exception("analysis not ready")

        return parse_info(analysis)


def run(path: str):
    gtp = KataGo()
    gtp.load_sgf(path)
    pprint(gtp.analyze())
    gtp.gtp.terminate()


if __name__ == "__main__":
    run(
        "/Users/oleksandr.hiliazov/PycharmProjects/tsumegolab/tsumegolab/tsumego.sgf"
    )
