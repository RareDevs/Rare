import json
import logging
import webbrowser

from PyQt5.QtCore import QLocale, QUrl, QJsonDocument, QJsonParseError
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QWidget

from rare.ui.components.tabs.store.shop_game_info import Ui_shop_info
from rare.utils import models


class ShopGameInfo(QWidget, Ui_shop_info):
    game: models.ShopGame
    data: dict

    # TODO GANZ VIEL
    def __init__(self):
        super(ShopGameInfo, self).__init__()
        self.setupUi(self)
        self.open_store_button.clicked.connect(self.button_clicked)
        self.manager = QNetworkAccessManager()

    def update_game(self, data: dict):
        slug = data["productSlug"]
        if "/home" in slug:
            slug = slug.replace("/home", "")
        self.slug = slug
        self.title.setText(data["title"])
        self.price.setText(data['price']['totalPrice']['fmtPrice']['originalPrice'])
        self.dev.setText(self.tr("Loading"))
        self.image.setPixmap(QPixmap())
        self.data = data

        # init API request
        locale = QLocale.system().name().split("_")[0]
        url = f"https://store-content.ak.epicgames.com/api/{locale}/content/products/{slug}"
        # game = api_utils.get_product(slug, locale)
        self.request = self.manager.get(QNetworkRequest(QUrl(url)))
        self.request.finished.connect(self.data_received)
        # self.request.finished.connect(self.request.deleteLater if self.request else None)

    def data_received(self):
        logging.info(f"Data of game {self.data['title']} received")
        if self.request:
            if self.request.error() == QNetworkReply.NoError:
                error = QJsonParseError()
                json_data = QJsonDocument.fromJson(self.request.readAll().data(), error)

                if error.error == error.NoError:
                    game = json.loads(json_data.toJson().data().decode())
                else:
                    logging.info(self.slug, error.errorString())
                    return
            else:
                return
        else:
            return
        self.game = models.ShopGame.from_json(game, self.data)
        # print(game)
        self.title.setText(self.game.title)
        """
        if not os.path.exists(path := os.path.expanduser(f"~/.cache/rare/cache/{self.game.title}.png")):
            url = game["pages"][0]["_images_"][0]
            open(os.path.expanduser(path), "wb").write(requests.get(url).content)
        width = 360
        self.image.setPixmap(QPixmap(path).scaled(width, int(width * 9 / 16), transformMode=Qt.SmoothTransformation))
        """
        try:
            self.dev.setText(",".join(self.game.developer))
        except KeyError:
            pass

        # self.price.setText(self.game.price)

        self.request.deleteLater()

    def button_clicked(self):
        webbrowser.open("https://www.epicgames.com/store/de/p/" + self.slug)
