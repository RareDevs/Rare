from legendary.core import LegendaryCore

from rare.shared import RareCore
from rare.utils.paths import cache_dir
from rare.widgets.side_tab import SideTabWidget
from .game_info import ShopGameInfo
from .search_results import SearchResults
from .shop_api_core import ShopApiCore
from .shop_widget import ShopWidget
from .wishlist import WishlistWidget, Wishlist


class StoreTab(SideTabWidget):

    def __init__(self, core: LegendaryCore, parent=None):
        super(StoreTab, self).__init__(parent=parent)
        self.init = False

        self.core = core
        # self.rcore = RareCore.instance()
        self.api_core = ShopApiCore(
            self.core.egs.session.headers["Authorization"],
            self.core.language_code,
            self.core.country_code,
        )

        self.shop = ShopWidget(cache_dir(), self.core, self.api_core, parent=self)
        self.shop_index = self.addTab(self.shop, self.tr("Games"))
        self.shop.show_game.connect(self.show_game)
        self.shop.show_info.connect(self.show_search)

        self.search = SearchResults(self.api_core, parent=self)
        self.search_index = self.addTab(self.search, self.tr("Search"))
        self.search.show_info.connect(self.show_game)
        # self.search.back_button.clicked.connect(lambda: self.setCurrentIndex(self.shop_index))

        self.info = ShopGameInfo(
            # [i.asset_infos["Windows"].namespace for i in self.rcore.game_list if bool(i.asset_infos)],
            [],
            self.api_core,
            parent=self
        )
        self.info_index = self.addTab(self.info, self.tr("Information"))
        # self.info.back_button.clicked.connect(lambda: self.setCurrentIndex(self.previous_index))

        self.wishlist = Wishlist(self.api_core, parent=self)
        self.wishlist_index = self.addTab(self.wishlist, self.tr("Wishlist"))
        self.wishlist.update_wishlist_signal.connect(self.update_wishlist)
        self.wishlist.show_game_info.connect(self.show_game)

        self.api_core.update_wishlist.connect(self.update_wishlist)

        self.previous_index = self.shop_index

    def update_wishlist(self):
        self.shop.update_wishlist()

    def load(self):
        if not self.init:
            self.init = True
            self.shop.load()
            self.wishlist.update_wishlist()

    def show_game(self, data):
        self.previous_index = self.currentIndex()
        self.info.update_game(data)
        self.setCurrentIndex(self.info_index)

    def show_search(self, text: str):
        self.search.load_results(text)
        self.setCurrentIndex(self.search_index)
