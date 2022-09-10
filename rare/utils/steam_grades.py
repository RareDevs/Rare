import difflib
import json
import os
from datetime import date

import requests
from PyQt5.QtCore import pyqtSignal, QRunnable, QObject, QCoreApplication

from rare.lgndr.core import LegendaryCore
from rare.shared import LegendaryCoreSingleton, ArgumentsSingleton
from rare.utils.paths import data_dir, cache_dir

replace_chars = ",;.:-_ "
url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"


class SteamWorker(QRunnable):
    class Signals(QObject):
        rating = pyqtSignal(str)

    app_name: str = ""

    def __init__(self, core: LegendaryCore):
        super(SteamWorker, self).__init__()
        self.signals = SteamWorker.Signals()
        self.core = core
        _tr = QCoreApplication.translate
        self.ratings = {
            "platinum": _tr("SteamWorker", "Platinum"),
            "gold": _tr("SteamWorker", "Gold"),
            "silver": _tr("SteamWorker", "Silver"),
            "bronze": _tr("SteamWorker", "Bronze"),
            "fail": _tr("SteamWorker", "Could not get grade"),
            "borked": _tr("SteamWorker", "unplayable"),
            "pending": _tr("SteamWorker", "Could not get grade"),
        }

    def set_app_name(self, app_name: str):
        self.app_name = app_name

    def run(self) -> None:
        self.signals.rating.emit(
            self.ratings.get(get_rating(self.app_name), self.ratings["fail"])
        )


__steam_ids_json = None
__grades_json = None


def get_rating(app_name: str):
    core = LegendaryCoreSingleton()
    args = ArgumentsSingleton()
    global __grades_json
    if __grades_json is None:
        if os.path.exists(p := os.path.join(data_dir(), "steam_ids.json")):
            grades = json.loads(open(p).read())
            __grades_json = grades
        else:
            grades = {}
            __grades_json = grades
    else:
        grades = __grades_json

    if not grades.get(app_name):
        if args.offline:
            return "pending"
        game = core.get_game(app_name)

        steam_id = get_steam_id(game.app_title)
        grade = get_grade(steam_id)
        grades[app_name] = {"steam_id": steam_id, "grade": grade}
        with open(os.path.join(data_dir(), "steam_ids.json"), "w") as f:
            f.write(json.dumps(grades))
            f.close()
        return grade
    else:
        return grades[app_name].get("grade")


# you should iniciate the module with the game's steam code
def get_grade(steam_code):
    if steam_code == 0:
        return "fail"
    steam_code = str(steam_code)
    url = "https://www.protondb.com/api/v1/reports/summaries/"
    res = requests.get(f"{url}{steam_code}.json")
    try:
        lista = json.loads(res.text)
    except json.decoder.JSONDecodeError:
        return "fail"

    return lista["tier"]


def load_json() -> dict:
    file = os.path.join(cache_dir(), "game_list.json")
    if not os.path.exists(file):
        response = requests.get(url)
        steam_ids = json.loads(response.text)["applist"]["apps"]
        ids = {}
        for game in steam_ids:
            ids[game["name"]] = game["appid"]

        with open(file, "w") as f:
            f.write(json.dumps(ids))
            f.close()
        return ids
    else:
        return json.loads(open(file, "r").read())


def get_steam_id(title: str):
    file = os.path.join(cache_dir(), "game_list.json")
    # workarounds for satisfactory
    title = title.replace("Early Access", "").replace("Experimental", "").strip()
    global __steam_ids_json
    if __steam_ids_json is None:
        if not os.path.exists(file):
            response = requests.get(url)
            ids = {}
            steam_ids = json.loads(response.text)["applist"]["apps"]
            for game in steam_ids:
                ids[game["name"]] = game["appid"]
            __steam_ids_json = ids

            with open(file, "w") as f:
                f.write(json.dumps(ids))
                f.close()
        else:
            ids = json.loads(open(file, "r").read())
            __steam_ids_json = ids
    else:
        ids = __steam_ids_json

    if title in ids.keys():
        steam_name = [title]

    else:
        steam_name = difflib.get_close_matches(title, ids.keys(), n=1)
    if steam_name:
        return ids[steam_name[0]]
    else:
        return 0


def check_time():  # this function check if it's time to update
    file = os.path.join(cache_dir(), "game_list.json")
    json_table = json.loads(open(file, "r").read())

    today = date.today()
    day = 0  # it controls how many days it's necessary for an update
    for i in "ymd":
        if i == "d":
            day = 7
        else:
            day = 0
        if int(today.strftime("%" + i)) > int(json_table["data"][i]) + day:
            return 1
        else:
            return 0
