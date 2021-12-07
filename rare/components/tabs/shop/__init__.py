from PyQt5.QtWidgets import QStackedWidget, QTabWidget

from legendary.core import LegendaryCore
from rare import cache_dir, shared
from rare.components.tabs.shop.game_info import ShopGameInfo
from rare.components.tabs.shop.search_results import SearchResults
from rare.components.tabs.shop.shop_api_core import ShopApiCore
from rare.components.tabs.shop.shop_widget import ShopWidget
from rare.components.tabs.shop.wishlist import WishlistWidget, Wishlist


class Shop(QStackedWidget):
    init = False

    def __init__(self, core: LegendaryCore):
        super(Shop, self).__init__()
        self.core = core
        self.api_core = ShopApiCore(self.core.egs.session.headers["Authorization"], self.core.language_code,
                                    self.core.country_code)

        self.shop = ShopWidget(cache_dir, core, self.api_core)
        self.wishlist_widget = Wishlist(self.api_core)

        self.store_tabs = QTabWidget()
        self.store_tabs.addTab(self.shop, self.tr("Games"))
        self.store_tabs.addTab(self.wishlist_widget, self.tr("Wishlist"))

        self.addWidget(self.store_tabs)

        self.search_results = SearchResults(self.api_core)
        self.addWidget(self.search_results)
        self.search_results.show_info.connect(self.show_game_info)
        self.info = ShopGameInfo([i.asset_infos["Windows"].namespace for i in shared.api_results.game_list], self.api_core)
        self.addWidget(self.info)
        self.info.back_button.clicked.connect(lambda: self.setCurrentIndex(0))

        self.search_results.back_button.clicked.connect(lambda: self.setCurrentIndex(0))
        self.shop.show_info.connect(self.show_search_results)

        self.wishlist_widget.show_game_info.connect(self.show_game_info)
        self.shop.show_game.connect(self.show_game_info)
        self.api_core.update_wishlist.connect(self.update_wishlist)
        self.wishlist_widget.update_wishlist_signal.connect(self.update_wishlist)

    def update_wishlist(self):
        self.shop.update_wishlist()

    def load(self):
        if not self.init:
            self.init = True
            self.shop.load()
            self.wishlist_widget.update_wishlist()

    def show_game_info(self, data):
        self.info.update_game(data)
        self.setCurrentIndex(2)

    def show_search_results(self, text: str):
        self.search_results.load_results(text)
        self.setCurrentIndex(1)
