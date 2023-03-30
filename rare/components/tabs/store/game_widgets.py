import logging

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QMouseEvent
from PyQt5.QtWidgets import QWidget

from rare.components.tabs.store.shop_models import ImageUrlModel
from rare.shared.image_manager import ImageSize
from rare.ui.components.tabs.store.wishlist_widget import Ui_WishlistWidget
from rare.utils.extra_widgets import ImageLabel
from rare.utils.misc import qta_icon
from .image_widget import ShopImageWidget

logger = logging.getLogger("GameWidgets")


class GameWidget(ShopImageWidget):
    show_info = pyqtSignal(dict)

    def __init__(self, path, json_info=None, parent=None):
        super(GameWidget, self).__init__(parent=parent)
        self.setFixedSize(ImageSize.Wide)
        self.ui.setupUi(self)
        self.path = path
        self.json_info = json_info
        if json_info:
            self.init_ui(json_info)

    def init_ui(self, json_info):
        if not json_info:
            self.ui.title_label.setText(self.tr("An error occurred"))
            return

        self.ui.title_label.setText(json_info.get("title"))
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
                self.fetchPixmap(img["url"], json_info["id"], json_info["title"])
                break
        else:
            logger.info(", ".join([img["type"] for img in json_info["keyImages"]]))

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            a0.accept()
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
        original_price = game["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
        discount_price = game["price"]["totalPrice"]["fmtPrice"]["discountPrice"]

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
        self.delete_button.clicked.connect(
            lambda: self.delete_from_wishlist.emit(self.game)
        )

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        # left button
        if e.button() == 1:
            self.open_game.emit(self.game)
        # right
        elif e.button() == 2:
            pass  # self.showMenu(e)
