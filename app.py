from pathlib import Path

from src import create_app

app = create_app(Path("./config.toml").resolve())
