import requests
from PyQt5.QtCore import QThread, pyqtSignal

from custom_legendary.core import LegendaryCore
from rare.components.tabs.shop.browse_games import game_query
from rare.components.tabs.shop.shop_models import ShopGame
from rare.utils.utils import get_lang


class AnalyzeThread(QThread):
    get_tags = pyqtSignal(dict)

    def __init__(self, core: LegendaryCore):
        super(AnalyzeThread, self).__init__()
        self.tags = {}
        self.core = core

    def run(self) -> None:
        locale = get_lang()
        for igame in self.core.get_installed_list():
            data = {
                "query": game_query,
                "variables": {"category": "games/edition/base|bundles/games|editors|software/edition/base",
                              "count": 20,
                              "country": locale.upper(), "keywords": igame.title, "locale": locale, "sortDir": "DESC",
                              "allowCountries": locale.upper(),
                              "start": 0, "tag": "", "withMapping": False, "withPrice": True}
            }

            try:
                search_game = \
                requests.post("https://www.epicgames.com/graphql", json=data).json()["data"]["Catalog"]["searchStore"][
                    "elements"][0]
            except:
                continue
            slug = search_game["productSlug"]
            is_bundle = False
            for i in search_game["categories"]:
                if "bundles" in i.get("path", ""):
                    is_bundle = True

            api_game = requests.get(
                f"https://store-content.ak.epicgames.com/api/{locale}/content/{'products' if not is_bundle else 'bundles'}/{slug}").json()

            if api_game.get("error"):
                print(igame.title)
                continue

            game = ShopGame.from_json(api_game, search_game)

            for i in game.tags:
                if i not in self.tags.keys():
                    self.tags[i] = 1
                else:
                    self.tags[i] += 1

        print(self.tags)
