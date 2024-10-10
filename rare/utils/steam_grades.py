import difflib
import os
from datetime import datetime
from enum import Enum
from logging import getLogger
from typing import Tuple

import orjson
import requests

from rare.lgndr.core import LegendaryCore
from rare.utils.paths import cache_dir

logger = getLogger("SteamGrades")

replace_chars = ",;.:-_ "
steamapi_url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
protondb_url = "https://www.protondb.com/api/v1/reports/summaries/"

__steam_ids_json = None
__grades_json = None
__active_download = False


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


def get_rating(core: LegendaryCore, app_name: str) -> Tuple[int, str]:
    game = core.get_game(app_name)
    try:
        steam_id = get_steam_id(game.app_title)
        if not steam_id:
            raise Exception
        grade = get_grade(steam_id)
    except Exception:
        logger.error("Failed to get ProtonDB rating for %s", game.app_title)
        return 0, "fail"
    else:
        return steam_id, grade


# you should initiate the module with the game's steam code
def get_grade(steam_code):
    if steam_code == 0:
        return "fail"
    steam_code = str(steam_code)
    res = requests.get(f"{protondb_url}{steam_code}.json")
    try:
        app = orjson.loads(res.text)
    except orjson.JSONDecodeError as e:
        logger.error("Failed to get ProtonDB response for %s", steam_code)
        return "fail"

    return app.get("tier", "fail")


def load_json() -> dict:
    global __active_download
    if __active_download:
        return {}
    file = os.path.join(cache_dir(), "steam_appids.json")
    elapsed_days = 0
    if os.path.exists(file):
        mod_time = datetime.fromtimestamp(os.path.getmtime(file))
        elapsed_days = abs(datetime.now() - mod_time).days
    if not os.path.exists(file) or elapsed_days > 7:
        __active_download = True
        response = requests.get(steamapi_url)
        __active_download = False
        apps = orjson.loads(response.text).get("applist", {}).get("apps", {})
        ids = {}
        for app in apps:
            ids[app["name"]] = app["appid"]
        with open(file, "w", encoding="utf-8") as f:
            f.write(orjson.dumps(ids).decode("utf-8"))
        return ids
    else:
        return orjson.loads(open(file, "r").read())


def get_steam_id(title: str) -> int:
    # workarounds for satisfactory
    # FIXME: This has to be made smarter.
    title = title.replace("Early Access", "").replace("Experimental", "").strip()
    # title = title.split(":")[0]
    # title = title.split("-")[0]
    global __steam_ids_json
    if __steam_ids_json is None:
        __steam_ids_json = load_json()
    ids = __steam_ids_json

    if title in ids.keys():
        steam_name = [title]
    else:
        steam_name = difflib.get_close_matches(title, ids.keys(), n=1, cutoff=0.5)
    if steam_name:
        return ids[steam_name[0]]
    else:
        return 0
