import logging
import os

import requests
import json
from datetime import date


replace_chars = ",;.:-_ "

file = os.path.expanduser("~/.cache/rare/game_list.json")
url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

def get_id(game_name):
    global file

    if check_time() == 1:
        upgrade_content()

    text = open(file, 'r')
    game_list = json.load(text)
    
    return game_list[game_name.lower()]


def upgrade_content(games: list):  # this function uploads the ids database, aka game_list.json
    global url
    global file
    response = requests.get(url)
    content = json.loads(response.text)
    game_list = {}  # {CrabEA: {id: 1234, grade: platinum}, ..}

    steam_games = {}
    for i in content["applist"]["apps"]:
        name: str = i["name"].lower()
        for c in replace_chars:
            name = name.replace(c, "")
        name = name.encode("ascii", "ignore").decode("ascii", "ignore")
        steam_games[name] = i["appid"]

    for i in games:
        if i.app_title.lower() in steam_games.keys():
            game_list[i.app_name] = {}
            game_list[i.app_name]["id"] = steam_games[i.app_title.lower()]
            continue
        else:
            app_title = i.app_title.lower()
            app_title = app_title.encode("ascii", "ignore").decode("ascii", "ignore")
            for c in replace_chars:
                app_title = app_title.replace(c, "")
            if app_title in steam_games.keys():
                game_list[i.app_name] = {}
                game_list[i.app_name]["id"] = steam_games[app_title]
            else:
                for game in steam_games:
                    if app_title.startswith(game):
                        game_list[i.app_name] = {}
                        game_list[i.app_name]["id"] = steam_games[game]

    for game in game_list:
        try:
            grade = get_grade(game_list[game]["id"])
        except json.decoder.JSONDecodeError as e:
            logging.error(str(e))
            game_list[game]["grade"] = "fail"
            print(game)  # debug
        else:
            game_list[game]["grade"] = grade

    print(game_list)

    # print(game_list)

    # for game in content['applist']['apps']:
    #    game_list[game['name'].lower()] = game['appid']

    # uploding date on json
    today = date.today()
    game_list['data']  = {}
    for i in "ymd":
        game_list["data"][i] = today.strftime('%' + i)

    table = open(file, 'w')

    json.dump(game_list, table)
    table.close()


def check_time():  # this function check if it's time to update
    global file
    text = open(file, 'r')
    json_table = json.load(text)
    text.close()

    today = date.today()
    day = 0 # it controls how many days it's necessary for an update
    for i in 'ymd':
        if i == 'd':
            day = 7
        else:
            day = 0
        if int(today.strftime('%' + i)) > int(json_table['data'][i]) + day:
            return 1
        else:
            return 0


# you should iniciate the module with the game's steam code
def get_grade(steam_code):
    steam_code = str(steam_code)
    url = 'https://www.protondb.com/api/v1/reports/summaries/'
    res = requests.get(url + steam_code + '.json')
    text = res.text
    lista = json.loads(text)
    # print(lista['tier'])  # just for debug pourpouses!!!

    return lista['tier']


def id(game_name):
    return get_grade(get_id(game_name))
