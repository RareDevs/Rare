import json
import logging
import webbrowser

from PyQt5.QtCore import QLocale, QUrl, QJsonDocument, QJsonParseError, Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QWidget, QLabel
from rare.utils.utils import get_lang

from rare.utils.extra_widgets import WaitingSpinner

from rare.components.tabs.shop.shop_models import ShopGame
from rare.ui.components.tabs.store.shop_game_info import Ui_shop_info

logger = logging.getLogger("ShopInfo")


class ShopGameInfo(QWidget, Ui_shop_info):
    game: ShopGame
    data: dict

    # TODO Design
    def __init__(self):
        super(ShopGameInfo, self).__init__()
        self.setupUi(self)
        self.open_store_button.clicked.connect(self.button_clicked)
        self.image_stack.addWidget(WaitingSpinner())
        self.manager = QNetworkAccessManager()

    def update_game(self, data: dict):
        self.image_stack.setCurrentIndex(1)
        for i in reversed(range(self.req_group_box.layout().count())):
            self.req_group_box.layout().itemAt(i).widget().setParent(None)
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
        locale = get_lang()
        locale = "en"
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
        # print(self.game.reqs)
        bold_font = QFont()
        bold_font.setBold(True)
        min_label = QLabel(self.tr("Minimum"))
        min_label.setFont(bold_font)
        rec_label = QLabel(self.tr("Recommend"))
        rec_label.setFont(bold_font)
        self.req_group_box.layout().addWidget(min_label, 0, 1)
        self.req_group_box.layout().addWidget(rec_label, 0, 2)

        for i, (key, value) in enumerate(self.game.reqs["Windows"].items()):
            self.req_group_box.layout().addWidget(QLabel(key), i+1, 0)
            min_label = QLabel(value[0])
            min_label.setWordWrap(True)
            self.req_group_box.layout().addWidget(min_label, i+1, 1)
            rec_label = QLabel(value[1])
            rec_label.setWordWrap(True)
            self.req_group_box.layout().addWidget(rec_label, i+1, 2)

        self.image_request = self.manager.get(QNetworkRequest(QUrl(self.game.image_urls.offer_image_tall)))
        self.image_request.finished.connect(self.image_loaded)

        try:
            if isinstance(self.game.developer, list):
                self.dev.setText(", ".join(self.game.developer))
            else:
                self.dev.setText(self.game.developer)
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
            self.image_stack.setCurrentIndex(0)
        else:
            logger.error("Load image failed")

    def button_clicked(self):
        webbrowser.open("https://www.epicgames.com/store/de/p/" + self.slug)

