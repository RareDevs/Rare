import json
import logging
import webbrowser

from PyQt5.QtCore import QUrl, QJsonDocument, QJsonParseError
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QWidget, QLabel

from rare.components.tabs.shop.shop_models import ShopGame
from rare.ui.components.tabs.store.shop_game_info import Ui_shop_info
from rare.utils.extra_widgets import WaitingSpinner, ImageLabel
from rare.utils.utils import get_lang

logger = logging.getLogger("ShopInfo")


class ShopGameInfo(QWidget, Ui_shop_info):
    game: ShopGame
    data: dict

    # TODO Design
    def __init__(self, installed_titles: list):
        super(ShopGameInfo, self).__init__()
        self.setupUi(self)
        self.installed = installed_titles
        self.open_store_button.clicked.connect(self.button_clicked)
        self.image = ImageLabel()
        self.image_stack.addWidget(self.image)
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
        if data["namespace"] in self.installed:
            self.open_store_button.setText(self.tr("Show Game on Epic Page"))
            self.owned_label.setVisible(True)
        else:
            self.open_store_button.setText(self.tr("Buy Game in Epic Games Store"))
            self.owned_label.setVisible(False)

        self.dev.setText(self.tr("Loading"))
        self.image.setPixmap(QPixmap())
        self.data = data
        is_bundle = False
        for i in data["categories"]:
            if "bundles" in i.get("path", ""):
                is_bundle = True

        # init API request
        locale = get_lang()
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
        self.title.setText(self.game.title)
        if self.game.price != "0":
            self.price.setText(self.game.price)
        else:
            self.price.setText(self.tr("Free"))
        if self.game.price != self.game.discount_price:
            self.discount_price.setText(self.game.discount_price)
            self.discount_price.setVisible(True)
        else:
            self.discount_price.setVisible(False)
        # print(self.game.reqs)
        bold_font = QFont()
        bold_font.setBold(True)
        min_label = QLabel(self.tr("Minimum"))
        min_label.setFont(bold_font)
        rec_label = QLabel(self.tr("Recommend"))
        rec_label.setFont(bold_font)

        if self.game.reqs:
            self.req_group_box.layout().addWidget(min_label, 0, 1)
            self.req_group_box.layout().addWidget(rec_label, 0, 2)
            for i, (key, value) in enumerate(self.game.reqs.get("Windows", {}).items()):
                self.req_group_box.layout().addWidget(QLabel(key), i + 1, 0)
                min_label = QLabel(value[0])
                min_label.setWordWrap(True)
                self.req_group_box.layout().addWidget(min_label, i + 1, 1)
                rec_label = QLabel(value[1])
                rec_label.setWordWrap(True)
                self.req_group_box.layout().addWidget(rec_label, i + 1, 2)
        else:
            self.req_group_box.layout().addWidget(QLabel(self.tr("Could not get requirements")))

        self.image.update_image(self.game.image_urls.front_tall, self.game.title, (240, 320))

        self.image_stack.setCurrentIndex(0)
        # self.image_request = self.manager.get(QNetworkRequest(QUrl(self.game.image_urls.offer_image_tall)))
        # self.image_request.finished.connect(self.image_loaded)

        try:
            if isinstance(self.game.developer, list):
                self.dev.setText(", ".join(self.game.developer))
            else:
                self.dev.setText(self.game.developer)
        except KeyError:
            pass
        self.tags.setText(", ".join(self.game.tags))
        # self.price.setText(self.game.price)

        self.request.deleteLater()

    def button_clicked(self):
        webbrowser.open("https://www.epicgames.com/store/de/p/" + self.slug)
