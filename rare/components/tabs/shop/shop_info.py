import json
import logging
import webbrowser

from PyQt5.QtCore import QLocale, QUrl, QJsonDocument, QJsonParseError, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QWidget

from rare.components.tabs.shop.shop_models import ShopGame
from rare.ui.components.tabs.store.shop_game_info import Ui_shop_info

logger = logging.getLogger("ShopInfo")


class ShopGameInfo(QWidget, Ui_shop_info):
    game: ShopGame
    data: dict

    # TODO Design; More information(requirements, more images); bundles (eg EA triple)
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

        self.dev.setText(self.tr("Loading"))
        self.image.setPixmap(QPixmap())
        self.data = data
        is_bundle = False
        for i in data["categories"]:
            if "bundles" in i.get("path", ""):
                is_bundle = True

        # init API request
        locale = QLocale.system().name().split("_")[0]
        url = f"https://store-content.ak.epicgames.com/api/{locale}/content/{'products' if not is_bundle else 'bundles'}/{slug}"
        # game = api_utils.get_product(slug, locale)
        self.request = self.manager.get(QNetworkRequest(QUrl(url)))
        self.request.finished.connect(self.data_received)

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
                logger.error("Data failed")
                return
        else:
            return
        self.game = ShopGame.from_json(game, self.data)
        # print(game)
        self.title.setText(self.game.title)

        self.price.setText(self.game.price)
        self.discount_price.setText(self.game.discount_price)

        self.image_request = self.manager.get(QNetworkRequest(QUrl(self.game.image_urls.offer_image_tall)))
        self.image_request.finished.connect(self.image_loaded)

        try:
            self.dev.setText(",".join(self.game.developer))
        except KeyError:
            pass

        # self.price.setText(self.game.price)

        self.request.deleteLater()

    def image_loaded(self):
        if self.image_request and self.image_request.error() == QNetworkReply.NoError:
            data = self.image_request.readAll().data()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.image.setPixmap(pixmap.scaled(240, 320, transformMode=Qt.SmoothTransformation))
        else:
            logger.error("Load image failed")

    def button_clicked(self):
        webbrowser.open("https://www.epicgames.com/store/de/p/" + self.slug)

