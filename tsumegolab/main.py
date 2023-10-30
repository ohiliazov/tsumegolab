from pathlib import Path
from typing import Optional

from typer import Typer

cli = Typer(name="Tsumego Lab CLI")


@cli.command()
def tsumego_frame(input_sgf_path: Path, output_sgf_path: Optional[Path]):
    print(input_sgf_path.absolute())
    print(output_sgf_path.absolute())


@cli.command()
def validate():
    pass


if __name__ == "__main__":
    cli()
