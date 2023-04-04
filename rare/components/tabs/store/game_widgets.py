import logging

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QPushButton

from rare.components.tabs.store.shop_models import ImageUrlModel
from rare.shared.image_manager import ImageSize
from rare.utils.misc import icon
from rare.utils.qt_requests import QtRequestManager
from .image_widget import ShopImageWidget

logger = logging.getLogger("GameWidgets")


class GameWidget(ShopImageWidget):
    show_info = pyqtSignal(dict)

    def __init__(self, manager: QtRequestManager, json_info=None, parent=None):
        super(GameWidget, self).__init__(manager, parent=parent)
        self.setFixedSize(ImageSize.Wide)
        self.ui.setupUi(self)
        self.json_info = json_info
        if json_info:
            self.init_ui(json_info)

    def init_ui(self, json_info):
        if not json_info:
            self.ui.title_label.setText(self.tr("An error occurred"))
            return

        self.ui.title_label.setText(json_info.get("title"))
        for attr in json_info["customAttributes"]:
            if attr["key"] == "developerName":
                developer = attr["value"]
                break
        else:
            developer = json_info["seller"]["name"]
        self.ui.developer_label.setText(developer)
        price = json_info["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
        discount_price = json_info["price"]["totalPrice"]["fmtPrice"]["discountPrice"]
        self.ui.price_label.setText(f'{price if price != "0" else self.tr("Free")}')
        if price != discount_price:
            font = self.ui.price_label.font()
            font.setStrikeOut(True)
            self.ui.price_label.setFont(font)
            self.ui.discount_label.setText(f'{discount_price if discount_price != "0" else self.tr("Free")}')
        else:
            self.ui.discount_label.setVisible(False)

        for c in r'<>?":|\/*':
            json_info["title"] = json_info["title"].replace(c, "")

        for img in json_info["keyImages"]:
            if img["type"] in ["DieselStoreFrontWide", "OfferImageWide", "VaultClosed", "ProductLogo",]:
                if img["type"] == "VaultClosed" and json_info["title"] != "Mystery Game":
                    continue
                self.fetchPixmap(img["url"])
                break
        else:
            logger.info(", ".join([img["type"] for img in json_info["keyImages"]]))

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            a0.accept()
            self.show_info.emit(self.json_info)


class WishlistWidget(ShopImageWidget):
    open_game = pyqtSignal(dict)
    delete_from_wishlist = pyqtSignal(dict)

    def __init__(self, manager: QtRequestManager, game: dict, parent=None):
        super(WishlistWidget, self).__init__(manager, parent=parent)
        self.setFixedSize(ImageSize.Wide)
        self.ui.setupUi(self)
        self.game = game
        for attr in game["customAttributes"]:
            if attr["key"] == "developerName":
                developer = attr["value"]
                break
        else:
            developer = game["seller"]["name"]
        original_price = game["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
        discount_price = game["price"]["totalPrice"]["fmtPrice"]["discountPrice"]

        self.ui.title_label.setText(game.get("title"))
        self.ui.developer_label.setText(developer)
        self.ui.price_label.setText(f'{original_price if original_price != "0" else self.tr("Free")}')
        if original_price != discount_price:
            font = self.ui.price_label.font()
            font.setStrikeOut(True)
            self.ui.price_label.setFont(font)
            self.ui.discount_label.setText(f'{discount_price if discount_price != "0" else self.tr("Free")}')
        else:
            self.ui.discount_label.setVisible(False)
        image_model = ImageUrlModel.from_json(game["keyImages"])
        url = image_model.front_wide
        if not url:
            url = image_model.offer_image_wide
        self.fetchPixmap(url)

        self.delete_button = QPushButton(self)
        self.delete_button.setIcon(icon("mdi.delete", color="white"))
        self.delete_button.clicked.connect(
            lambda: self.delete_from_wishlist.emit(self.game)
        )
        self.layout().insertWidget(0, self.delete_button, alignment=Qt.AlignRight)

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        # left button
        if a0.button() == Qt.LeftButton:
            a0.accept()
            self.open_game.emit(self.game)
        # right
        elif a0.button() == Qt.RightButton:
            pass  # self.showMenu(e)
