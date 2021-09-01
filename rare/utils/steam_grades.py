import difflib
import json
import os
from datetime import date

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from custom_legendary.core import LegendaryCore
from rare import cache_dir, data_dir

replace_chars = ",;.:-_ "

file = os.path.join(cache_dir, "game_list.json")
url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"


class SteamWorker(QThread):
    app_name = ""
    rating_signal = pyqtSignal(str)

    def __init__(self, core: LegendaryCore):
        super(SteamWorker, self).__init__()
        self.core = core
        self.ratings = {"platinum": self.tr("Platinum"),
                        "gold": self.tr("Gold"),
                        "silver": self.tr("Silver"),
                        "bronze": self.tr("Bronze"),
                        "fail": self.tr("Could not get grade"),
                        "pending": self.tr("Could not get grade")
                        }

    def set_app_name(self, app_name: str):
        self.app_name = app_name

    def run(self) -> None:
        self.rating_signal.emit(self.ratings[get_rating(self.app_name, self.core)])


def get_rating(app_name: str, core: LegendaryCore):
    if os.path.exists(p := os.path.join(data_dir, "steam_ids.json")):
        grades = json.load(open(p))
    else:
        grades = {}

    if not grades.get(app_name):
        game = core.get_game(app_name)

        steam_id = get_steam_id(game.app_title)
        grade = get_grade(steam_id)
        grades[app_name] = {
            "steam_id": steam_id,
            "grade": grade
        }
        with open(os.path.join(data_dir, "steam_ids.json"), "w") as f:
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
    url = 'https://www.protondb.com/api/v1/reports/summaries/'
    res = requests.get(url + steam_code + '.json')
    try:
        lista = json.loads(res.text)
    except json.decoder.JSONDecodeError:
        return "fail"

    return lista['tier']


def load_json() -> dict:
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
    # workarounds for satisfactory
    title = title.replace("Early Access", "").replace("Experimental", "").strip()
    if not os.path.exists(file):
        response = requests.get(url)
        ids = {}
        steam_ids = json.loads(response.text)["applist"]["apps"]
        for game in steam_ids:
            ids[game["name"]] = game["appid"]

        with open(file, "w") as f:
            f.write(json.dumps(ids))
            f.close()
    else:
        ids = json.loads(open(file, "r").read())
    if title in ids.keys():
        steam_name = [title]
    else:
        steam_name = difflib.get_close_matches(title, ids.keys(), n=1)
    if steam_name:
        return ids[steam_name[0]]
    else:
        return 0


def check_time():  # this function check if it's time to update
    global file
    text = open(file, 'r')
    json_table = json.load(text)
    text.close()

    today = date.today()
    day = 0  # it controls how many days it's necessary for an update
    for i in 'ymd':
        if i == 'd':
            day = 7
        else:
            day = 0
        if int(today.strftime('%' + i)) > int(json_table['data'][i]) + day:
            return 1
        else:
            return 0
