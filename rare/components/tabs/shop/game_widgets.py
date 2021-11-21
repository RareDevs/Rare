import logging

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtNetwork import QNetworkAccessManager
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from qtawesome import icon

from rare.components.tabs.shop.shop_models import ImageUrlModel
from rare.ui.components.tabs.store.wishlist_widget import Ui_WishlistWidget
from rare.utils.extra_widgets import ImageLabel

logger = logging.getLogger("GameWidgets")


class GameWidget(QWidget):
    show_info = pyqtSignal(dict)

    def __init__(self, path, json_info=None, width=300):
        super(GameWidget, self).__init__()
        self.manager = QNetworkAccessManager()
        self.width = width
        self.path = path
        if json_info:
            self.init_ui(json_info)

    def init_ui(self, json_info):
        self.layout = QVBoxLayout()
        self.image = ImageLabel()
        self.layout.addWidget(self.image)
        mini_layout = QHBoxLayout()
        self.layout.addLayout(mini_layout)

        if not json_info:
            self.layout.addWidget(QLabel("An error occurred"))
            self.setLayout(self.layout)
            return

        self.title_label = QLabel(json_info.get("title"))
        self.title_label.setWordWrap(True)
        mini_layout.addWidget(self.title_label)
        mini_layout.addStretch(1)

        price = json_info['price']['totalPrice']['fmtPrice']['originalPrice']
        discount_price = json_info['price']['totalPrice']['fmtPrice']['discountPrice']
        price_label = QLabel(price)
        if price != discount_price:
            font = QFont()
            font.setStrikeOut(True)
            price_label.setFont(font)
            mini_layout.addWidget(QLabel(discount_price if discount_price != "0" else self.tr("Free")))
            mini_layout.addWidget(price_label)
        else:
            if price == "0":
                price_label.setText(self.tr("Free"))
            mini_layout.addWidget(price_label)

        for c in r'<>?":|\/*':
            json_info["title"] = json_info["title"].replace(c, "")

        self.json_info = json_info
        self.slug = json_info["productSlug"]

        self.title = json_info["title"]
        for img in json_info["keyImages"]:
            if img["type"] in ["DieselStoreFrontWide", "OfferImageWide", "VaultClosed", "ProductLogo"]:
                if img["type"] == "VaultClosed" and self.title != "Mystery Game":
                    continue
                self.image.update_image(img["url"], json_info["title"], (self.width, int(self.width * 9 / 16)))
                break
        else:
            logger.info(", ".join([img["type"] for img in json_info["keyImages"]]))

        self.setLayout(self.layout)

        self.setFixedSize(self.width + 10, self.width * 9 // 16 + 50)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.show_info.emit(self.json_info)


class WishlistWidget(QWidget, Ui_WishlistWidget):
    open_game = pyqtSignal(dict)
    delete_from_wishlist = pyqtSignal(dict)

    def __init__(self, game: dict):
        super(WishlistWidget, self).__init__()
        self.setupUi(self)
        self.game = game
        self.title_label.setText(game.get("title"))
        for attr in game["customAttributes"]:
            if attr["key"] == "developerName":
                self.developer.setText(attr["value"])
                break
        else:
            self.developer.setText(game["seller"]["name"])
        original_price = game['price']['totalPrice']['fmtPrice']['originalPrice']
        discount_price = game['price']['totalPrice']['fmtPrice']['discountPrice']

        self.price.setText(original_price if original_price != "0" else self.tr("Free"))
        # if discount
        if original_price != discount_price:
            self.discount = True
            font = QFont()
            font.setStrikeOut(True)
            self.price.setFont(font)
            self.discount_price.setText(discount_price)
        else:
            self.discount = False
            self.discount_price.setVisible(False)

        self.image = ImageLabel()
        self.layout().insertWidget(0, self.image)
        image_model = ImageUrlModel.from_json(game["keyImages"])
        url = image_model.front_wide
        if not url:
            url = image_model.offer_image_wide
        self.image.update_image(url, game.get("title"), (240, 135))
        self.delete_button.setIcon(icon("mdi.delete", color="white"))
        self.delete_button.clicked.connect(lambda: self.delete_from_wishlist.emit(self.game))

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        # left button
        if e.button() == 1:
            self.open_game.emit(self.game)
        # right
        elif e.button() == 2:
            pass  # self.showMenu(e)
