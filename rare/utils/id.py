import requests
import json
from datetime import date

file = "game_list.json"
url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"


def get_id(game_name):
    global file

    if check_time() == 1:
        upgrade_content()

    text = open(file, 'r')
    game_list = json.load(text)
    
    return game_list[game_name.lower()]


def test():
    #get_grade(get_id('MORDHAU'))
    return get_grade(get_id(input('Type a correct game name: ')))


def upgrade_content(): # this function uploads the ids database, aka game_list.json
    global url
    global file
    response = requests.get(url)
    content = json.loads(response.text)
    table = open(file, 'w')
    game_list = {}

    for game in content['applist']['apps']:
        game_list[game['name'].lower()] = game['appid']

    # uploding date on json
    today = date.today()
    game_list['data']  = {}
    for i in "ymd":
        game_list["data"][i] = today.strftime('%' + i)

    json.dump(game_list, table)
    table.close()


def check_time(): # this function check if it's time to update
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


#test()
