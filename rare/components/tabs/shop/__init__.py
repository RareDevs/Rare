from PyQt5.QtWidgets import QStackedWidget, QTabWidget

from custom_legendary.core import LegendaryCore
from rare import cache_dir
from rare.components.tabs.shop.browse_games import BrowseGames
from rare.components.tabs.shop.game_info import ShopGameInfo
from rare.components.tabs.shop.search_results import SearchResults
from rare.components.tabs.shop.shop_api_core import ShopApiCore
from rare.components.tabs.shop.shop_widget import ShopWidget


class Shop(QStackedWidget):
    init = False

    def __init__(self, core: LegendaryCore):
        super(Shop, self).__init__()
        self.core = core

        self.shop_api = ShopApiCore(self.core.egs.session.headers["Authorization"])

        self.shop = ShopWidget(cache_dir, core, self.shop_api)
        self.browse_games = BrowseGames(cache_dir, self.shop_api)

        self.store_tabs = QTabWidget()
        self.store_tabs.addTab(self.shop, self.tr("Games"))
        self.store_tabs.addTab(self.browse_games, self.tr("Browse"))
        self.store_tabs.tabBarClicked.connect(lambda x: self.browse_games.load() if x == 1 else None)

        self.addWidget(self.store_tabs)

        self.search_results = SearchResults(self.shop_api)
        self.addWidget(self.search_results)
        self.search_results.show_info.connect(self.show_game_info)

        self.info = ShopGameInfo([i.asset_info.namespace for i in self.core.get_game_list(True)], self.shop_api)
        self.addWidget(self.info)
        self.info.back_button.clicked.connect(lambda: self.setCurrentIndex(0))

        self.search_results.back_button.clicked.connect(lambda: self.setCurrentIndex(0))
        self.shop.show_info.connect(self.show_search_results)

        self.shop.show_game.connect(self.show_game_info)
        self.browse_games.show_game.connect(self.show_game_info)
        self.shop_api.update_wishlist.connect(self.update_wishlist)

    def update_wishlist(self):
        self.shop.update_wishlist()

    def load(self):
        if not self.init:
            self.init = True
            self.shop.load()

    def show_game_info(self, data):
        self.info.update_game(data)
        self.setCurrentIndex(2)

    def show_search_results(self, text: str):
        self.search_results.load_results(text)
        self.setCurrentIndex(1)
