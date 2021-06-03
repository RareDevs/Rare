import json
import logging
import os
import webbrowser
from json import JSONDecodeError

from PyQt5.QtCore import QLocale, Qt, QUrl
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QWidget

from rare.ui.components.tabs.store.shop_game_info import Ui_shop_info


class ShopGameInfo(QWidget, Ui_shop_info):
    slug = ""

    # TODO GANZ VIEL
    def __init__(self):
        super(ShopGameInfo, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.button_clicked)
        self.manager = QNetworkAccessManager()

    def update_game(self, slug: str):
        self.slug = slug
        locale = QLocale.system().name().split("_")[0]
        url = f"https://store-content.ak.epicgames.com/api/{locale}/content/products/{slug}"
        # game = api_utils.get_product(slug, locale)
        self.request = self.manager.get(QNetworkRequest(QUrl(url)))
        self.request.readyRead.connect(self.data_received)
        self.request.finished.connect(self.request.deleteLater if self.request else None)

    def data_received(self):
        logging.info(f"Data of game {self.slug} received")
        if self.request:
            if self.request.error() == QNetworkReply.NoError:
                try:
                    game = json.loads(self.request.readAll().data().decode())[0]
                except JSONDecodeError:
                    return
            else:
                return
        else:
            return
        self.title.setText(game["productName"])
        self.image.setPixmap(
            QPixmap(os.path.expanduser(f"~/.cache/rare/cache/{game['productName']}.png")).scaled(180,
                                                                                                 int(180 * 9 / 16),
                                                                                                 transformMode=Qt.SmoothTransformation))
        self.dev.setText(game["data"]["meta"]["developer"][0])

    def button_clicked(self):
        webbrowser.open("https://www.epicgames.com/store/de/p/" + self.slug)
