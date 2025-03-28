import difflib
import lzma
import os
from datetime import datetime
from enum import Enum
from logging import getLogger
from typing import Tuple, Dict

import orjson
import requests

from rare.lgndr.core import LegendaryCore
from rare.utils.paths import cache_dir

logger = getLogger("SteamGrades")

replace_chars = ",;.:-_ "
steamids_url = "https://raredevs.github.io/wring/steam_appids.json.xz"
protondb_url = "https://www.protondb.com/api/v1/reports/summaries/"

__steam_appids: Dict = None
__steam_titles: Dict = None
__steam_appids_version: int = 3
__active_download: bool = False


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


def get_rating(core: LegendaryCore, app_name: str, steam_appid: int = None) -> Tuple[int, str]:
    game = core.get_game(app_name)
    try:
        if steam_appid is None:
            steam_appid = get_steam_id(game.app_title)
            if not steam_appid:
                raise Exception
        grade = get_grade(steam_appid)
    except Exception as e:
        logger.exception(e)
        logger.error("Failed to get ProtonDB rating for %s", game.app_title)
        return 0, "fail"
    else:
        return steam_appid, grade


# you should initiate the module with the game's steam code
def get_grade(steam_code):
    if steam_code == 0:
        return "fail"
    steam_code = str(steam_code)
    res = requests.get(f"{protondb_url}{steam_code}.json")
    try:
        app = orjson.loads(res.text)
    except orjson.JSONDecodeError as e:
        logger.exception(e)
        logger.error("Failed to get ProtonDB response for %s", steam_code)
        return "fail"

    return app.get("tier", "fail")


def download_steam_appids() -> bytes:
    global __active_download
    if __active_download:
        return b""
    __active_download = True
    resp = requests.get(steamids_url)
    __active_download = False
    return resp.content


def load_steam_appids() -> Tuple[Dict, Dict]:
    global __steam_appids, __steam_titles

    if __steam_appids and __steam_titles:
        return __steam_appids, __steam_titles

    file = os.path.join(cache_dir(), "steam_appids.json")
    version = __steam_appids_version
    elapsed_days = 0

    if os.path.exists(file):
        mod_time = datetime.fromtimestamp(os.path.getmtime(file))
        elapsed_days = abs(datetime.now() - mod_time).days
        json = orjson.loads(open(file, "r").read())
        version = json.get("version", 0)
        if version >= __steam_appids_version:
            __steam_appids = json["games"]

    if not os.path.exists(file) or elapsed_days > 3 or version < __steam_appids_version:
        if content := download_steam_appids():
            text = lzma.decompress(content).decode("utf-8")
            with open(file, "w", encoding="utf-8") as f:
                f.write(text)
            json = orjson.loads(text)
            __steam_appids = json["games"]

    __steam_titles = {v: k for k, v in __steam_appids.items()}

    return __steam_appids, __steam_titles


def get_steam_id(title: str) -> int:
    # workarounds for satisfactory
    # FIXME: This has to be made smarter.
    title = title.replace("Early Access", "").replace("Experimental", "").strip()
    # title = title.split(":")[0]
    # title = title.split("-")[0]
    global __steam_appids, __steam_titles
    if not __steam_appids or not __steam_titles:
        __steam_appids, __steam_titles = load_steam_appids()

    if title in __steam_titles.keys():
        steam_name = [title]
    else:
        steam_name = difflib.get_close_matches(title, __steam_appids.keys(), n=1, cutoff=0.5)

    if steam_name:
        return __steam_appids[steam_name[0]]
    else:
        return 0
