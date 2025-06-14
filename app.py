import os

from src import create_app

app = create_app(os.path.abspath("config.json"))
