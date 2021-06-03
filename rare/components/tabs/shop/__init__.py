from PyQt5.QtWidgets import QStackedWidget, QWidget, QVBoxLayout, QLabel

from rare.components.tabs.shop.shop_info import ShopGameInfo
from rare.components.tabs.shop.shop_widget import ShopWidget


class Shop(QStackedWidget):
    init = False
    def __init__(self):
        super(Shop, self).__init__()

        self.shop = ShopWidget()
        self.addWidget(self.shop)

        self.info = ShopGameInfo()
        self.addWidget(self.info)

        self.shop.show_info.connect(self.show_info)

    def load(self):
        if not self.init:
            self.init = True
            self.shop.load()


    def show_info(self, slug):
        self.info.update_game(slug)
        self.setCurrentIndex(1)
