import json
import os
from dataclasses import dataclass
from datetime import datetime
from logging import getLogger
from typing import Dict

from rare import data_dir

logger = getLogger("GameMeta")


@dataclass
class GameMeta:
    app_name: str
    last_played: datetime = None

    @classmethod
    def from_json(cls, data):
        return cls(
            app_name=data["app_name"],
            last_played=datetime.strptime(data.get("last_played", "None"), '%Y-%m-%dT%H:%M:%S.%f')
        )

    def __dict__(self):
        return dict(
            app_name=self.app_name,
            last_played=self.last_played.strftime("%Y-%m-%dT%H:%M:%S.%f")
        )


class RareGameMeta:
    _meta: Dict[str, GameMeta] = {}

    def __init__(self):
        meta_data = {}
        if os.path.exists(p := os.path.join(data_dir, "game_meta.json")):
            try:
                meta_data = json.load(open(p))
            except json.JSONDecodeError:
                logger.warning("Game meta json file corrupt")
        else:
            with open(p, "w") as file:
                file.write("{}")

        for app_name, data in meta_data.items():
            self._meta[app_name] = GameMeta.from_json(data)

    def get_games(self):
        return list(self._meta.values())

    def get_game(self, app_name):
        return self._meta.get(app_name, GameMeta(app_name))

    def set_game(self, app_name: str, game: GameMeta):
        self._meta[app_name] = game
        self.save_file()

    def save_file(self):
        json.dump(
            {app_name: data.__dict__() for app_name, data in self._meta.items()},
            open(os.path.join(data_dir, "game_meta.json"), "w"),
            indent=4
        )
