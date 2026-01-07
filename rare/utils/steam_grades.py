import difflib
import lzma
import os
from datetime import datetime
from enum import Enum
from logging import getLogger
from typing import Dict, Tuple

import orjson
import requests

from rare.lgndr.core import LegendaryCore
from rare.utils.paths import cache_dir

logger = getLogger("SteamGrades")

class ProtondbRatings(int, Enum):
    # internal
    PENDING = ("pending", -2)
    FAIL = ("fail", -1)
    # protondb
    NA = ("na", 0)
    BORKED = ("borked", 1)
    BRONZE = ("bronze", 2)
    SILVER = ("silver", 3)
    GOLD = ("gold", 4)
    PLATINUM = ("platinum", 5)

    def __new__(cls, name: str, value: int):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj._name_ = name
        return obj

    def __str__(self):
        return self._name_

    def __int__(self):
        return self._value_


class SteamGrades:
    __steam_appids: Dict[str, str] = {}
    __steam_appids_version: int = 3
    __active_download: bool = False
    __replace_chars = ",;.:-_ "
    __steamids_url = "https://raredevs.github.io/wring/steam_appids.json.xz"
    __protondb_url = "https://www.protondb.com/api/v1/reports/summaries/"

    def __init__(self):
        pass

    def _download_steam_appids(self) -> bytes:
        if SteamGrades.__active_download:
            return b""
        SteamGrades.__active_download = True
        resp = requests.get(self.__steamids_url)
        SteamGrades.__active_download = False
        return resp.content

    def load_steam_appids(self) -> Dict:

        if SteamGrades.__steam_appids:
            return SteamGrades.__steam_appids

        file = os.path.join(cache_dir(), "steam_appids.json")
        version = SteamGrades.__steam_appids_version
        elapsed_days = 0

        if os.path.exists(file):
            mod_time = datetime.fromtimestamp(os.path.getmtime(file))
            elapsed_days = abs(datetime.now() - mod_time).days
            json = orjson.loads(open(file, "r").read())
            version = json.get("version", 0)
            if version >= SteamGrades.__steam_appids_version:
                SteamGrades.__steam_appids = json["games"]

        if not os.path.exists(file) or elapsed_days > 3 or version < SteamGrades.__steam_appids_version:
            if content := self._download_steam_appids():
                text = lzma.decompress(content).decode("utf-8")
                with open(file, "w", encoding="utf-8") as f:
                    f.write(text)
                json = orjson.loads(text)
                SteamGrades.__steam_appids = json["games"]

        return SteamGrades.__steam_appids

    @property
    def steam_appids(self) -> Dict[str, str]:
        if not SteamGrades.__steam_appids:
            SteamGrades.__steam_appids = self.load_steam_appids()
        return SteamGrades.__steam_appids

    @property
    def steam_titles(self) -> Dict:
        return {v: k for k, v in self.steam_appids.items()}

    def _get_steam_appid(self, title: str) -> str:
        # workarounds for satisfactory
        # FIXME: This has to be made smarter.
        title = title.replace("Early Access", "").replace("Experimental", "").strip()
        # title = title.split(":")[0]
        # title = title.split("-")[0]

        if title in self.steam_titles.keys():
            steam_name = [title]
        else:
            steam_name = difflib.get_close_matches(title, self.steam_appids.keys(), n=1, cutoff=0.5)

        if steam_name:
            return self.steam_appids[steam_name[0]]
        else:
            return "0"

    def _get_grade(self, steam_appid: str):
        if steam_appid == "0":
            return "fail"
        steam_appid = str(steam_appid)
        res = requests.get(f"{self.__protondb_url}/{steam_appid}.json")
        try:
            app = orjson.loads(res.text)
        except orjson.JSONDecodeError as e:
            logger.error(repr(e))
            logger.error("Failed to get ProtonDB response for %s", steam_appid)
            return "fail"

        return app.get("tier", "fail")

    def get_rating(self, core: LegendaryCore, app_name: str, steam_appid: str = None) -> Tuple[str, str]:
        game = core.get_game(app_name)
        try:
            if steam_appid is None:
                steam_appid = self._get_steam_appid(game.app_title)
                if not steam_appid:
                    raise RuntimeError
            grade = self._get_grade(steam_appid)
        except Exception as e:
            logger.error(repr(e))
            logger.error("Failed to get ProtonDB rating for %s", game.app_title)
            return "0", "fail"
        else:
            return steam_appid, grade
