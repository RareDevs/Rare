import requests
import json


def test():
    # get_grade(629760)
    get_grade(input('Game ID: '))


# you should iniciate the module with the game's steam code
def get_grade(steam_code):
    steam_code = str(steam_code)
    url = 'https://www.protondb.com/api/v1/reports/summaries/'
    res = requests.get(url + steam_code + '.json')
    text = res.text
    lista = json.loads(text)
    # print(lista['tier'])  # just for debug pourpouses!!!

    return lista['tier']


# test()
