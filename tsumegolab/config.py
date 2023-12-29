import shutil
from pathlib import Path

from loguru import logger
from pydantic import DirectoryPath, Field, FilePath
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ROOT = Path(__file__).parent.parent


def locate_katago_engine() -> Path:
    return Path(shutil.which("katago"))


class KataConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="kata_")

    engine_path: FilePath = Field(default_factory=locate_katago_engine)
    config_path: FilePath = APP_ROOT / "config" / "katago_analysis.cfg"
    output_path: DirectoryPath = APP_ROOT / "output"


class WebsocketConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ws_")

    host: str = "localhost"
    port: int = 15555


if __name__ == "__main__":
    kata_config = KataConfig()
    logger.info(kata_config)
