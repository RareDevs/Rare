from PyQt5.QtWidgets import QStackedWidget

from rare.components.tabs.shop.search_results import SearchResults
from rare.components.tabs.shop.shop_info import ShopGameInfo
from rare.components.tabs.shop.shop_widget import ShopWidget


class Shop(QStackedWidget):
    init = False

    def __init__(self):
        super(Shop, self).__init__()

        self.shop = ShopWidget()
        self.addWidget(self.shop)

        self.search_results = SearchResults()
        self.addWidget(self.search_results)
        self.search_results.show_info.connect(self.show_game_info)

        self.info = ShopGameInfo()
        self.addWidget(self.info)
        self.info.back_button.clicked.connect(lambda: self.setCurrentIndex(0))

        self.search_results.back_button.clicked.connect(lambda: self.setCurrentIndex(0))
        self.shop.show_info.connect(self.show_info)
        self.shop.show_game.connect(self.show_game_info)

    def load(self):
        if not self.init:
            self.init = True
            self.shop.load()

    def show_game_info(self, data):
        self.info.update_game(data)
        self.setCurrentIndex(2)

    def show_info(self, data):
        self.search_results.show_results(data)
        self.setCurrentIndex(1)
