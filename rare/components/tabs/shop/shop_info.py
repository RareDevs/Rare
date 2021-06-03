import os
import webbrowser

from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager
from PyQt5.QtWidgets import QWidget

from rare.ui.components.tabs.store.shop_game_info import Ui_shop_info
from rare.utils import api_utils


class ShopGameInfo(QWidget, Ui_shop_info):
    slug = ""

    def __init__(self):
        super(ShopGameInfo, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.button_clicked)
        self.manager = QNetworkAccessManager()

    def update_game(self, slug: str):
        locale = QLocale.system().name().split("_")[0]
        game = api_utils.get_product(slug, locale)
        self.slug = slug
        self.title.setText(game[0]["productName"])
        self.image.setPixmap(
            QPixmap(os.path.expanduser(f"~/.cache/rare/cache/{game[0]['productName']}.png")).scaled(180,
                                                                                                    int(180 * 9 / 16),
                                                                                                    transformMode=Qt.SmoothTransformation))

        self.dev.setText(game[0]["data"]["meta"]["developer"][0])

    def button_clicked(self):
        webbrowser.open("https://www.epicgames.com/store/de/p/" + self.slug)
