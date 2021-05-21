import difflib
import json
import os
from datetime import date

import requests
from PyQt5.QtCore import pyqtSignal

replace_chars = ",;.:-_ "

file = os.path.expanduser("~/.cache/rare/game_list.json")
url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"


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
    if not os.path.exists(p := os.path.expanduser("~/.cache/rare/steam_ids.json")):
        response = requests.get(url)
        steam_ids = json.loads(response.text)["applist"]["apps"]
        ids = {}
        for game in steam_ids:
            ids[game["name"]] = game["appid"]

        with open(os.path.expanduser(p), "w") as f:
            f.write(json.dumps(ids))
            f.close()
        return ids
    else:
        return json.loads(open(os.path.expanduser("~/.cache/rare/steam_ids.json"), "r").read())


def upgrade_all(games, progress: pyqtSignal = None):
    ids = load_json()
    data = {}
    for i, (title, app_name) in enumerate(games):
        title = title.replace("Early Access", "").replace("Experimental", "").strip()
        data[app_name] = {}

        steam_id = get_steam_id(title, ids)

        data[app_name] = {
            "steam_id": steam_id,
            "grade": get_grade(steam_id)}

        if progress:
            progress.emit(int(i / len(games) * 100))

    with open(os.path.expanduser("~/.cache/rare/game_list.json"), "w") as f:
        f.write(json.dumps(data))
        f.close()


def get_steam_id(title: str, json_data=None):
    title = title.replace("Early Access", "").replace("Experimental", "").strip()
    if not json_data:
        if not os.path.exists(p := os.path.expanduser("~/.cache/rare/steam_ids.json")):
            response = requests.get(url)
            ids = {}
            steam_ids = json.loads(response.text)["applist"]["apps"]
            for game in steam_ids:
                ids[game["name"]] = game["appid"]

            with open(os.path.expanduser(p), "w") as f:
                f.write(json.dumps(steam_ids))
                f.close()
        else:
            ids = json.loads(open(os.path.expanduser("~/.cache/rare/steam_ids.json"), "r").read())
    else:
        ids = json_data
    steam_name = difflib.get_close_matches(title, ids.keys(), n=1)
    if steam_name:
        return ids[steam_name[0]]
    else:
        return 0
    # print(x)

    # for game in steam_ids:
    #     num = difflib.SequenceMatcher(None, game["name"], title).ratio()
    #     if num > most_similar[2] and num > 0.5:
    #         most_similar = (game["appid"], game["name"], num)
    # print(time.time()-t)
    # name = difflib.get_close_matches(steam_ids.keys(), title)
    # return most_similar


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
