import logging

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QPushButton
from orjson import orjson

from rare.components.tabs.store.api.models.response import CatalogOfferModel
from rare.shared.image_manager import ImageSize
from rare.utils.misc import qta_icon
from rare.utils.qt_requests import QtRequestManager
from .api.debug import DebugDialog
from .image_widget import ShopImageWidget

logger = logging.getLogger("GameWidgets")


class GameWidget(ShopImageWidget):
    show_info = pyqtSignal(CatalogOfferModel)

    def __init__(self, manager: QtRequestManager, catalog_game: CatalogOfferModel = None, parent=None):
        super(GameWidget, self).__init__(manager, parent=parent)
        self.setFixedSize(ImageSize.Wide)
        self.ui.setupUi(self)
        self.catalog_game = catalog_game
        if catalog_game:
            self.init_ui(catalog_game)

    def init_ui(self, game: CatalogOfferModel):
        if not game:
            self.ui.title_label.setText(self.tr("An error occurred"))
            return

        self.ui.title_label.setText(game.title)
        for attr in game.custom_attributes:
            if attr["key"] == "developerName":
                developer = attr["value"]
                break
        else:
            developer = game.seller["name"]
        self.ui.developer_label.setText(developer)
        price = game.price.total_price["fmtPrice"]["originalPrice"]
        discount_price = game.price.total_price["fmtPrice"]["discountPrice"]
        self.ui.price_label.setText(f'{price if price != "0" else self.tr("Free")}')
        if price != discount_price:
            font = self.ui.price_label.font()
            font.setStrikeOut(True)
            self.ui.price_label.setFont(font)
            self.ui.discount_label.setText(f'{discount_price if discount_price != "0" else self.tr("Free")}')
        else:
            self.ui.discount_label.setVisible(False)

        key_images = game.key_images
        self.fetchPixmap(key_images.for_dimensions(self.width(), self.height()).url)

        # for img in json_info["keyImages"]:
        #     if img["type"] in ["DieselStoreFrontWide", "OfferImageWide", "VaultClosed", "ProductLogo"]:
        #         if img["type"] == "VaultClosed" and json_info["title"] != "Mystery Game":
        #             continue
        #         self.fetchPixmap(img["url"])
        #         break
        # else:
        #     logger.info(", ".join([img["type"] for img in json_info["keyImages"]]))

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            a0.accept()
            self.show_info.emit(self.catalog_game)
        if a0.button() == Qt.RightButton:
            a0.accept()
            print(self.catalog_game.__dict__)
            dialog = DebugDialog(self.catalog_game.__dict__, self)
            dialog.show()


class WishlistWidget(ShopImageWidget):
    open_game = pyqtSignal(CatalogOfferModel)
    delete_from_wishlist = pyqtSignal(CatalogOfferModel)

    def __init__(self, manager: QtRequestManager, catalog_game: CatalogOfferModel, parent=None):
        super(WishlistWidget, self).__init__(manager, parent=parent)
        self.setFixedSize(ImageSize.Wide)
        self.ui.setupUi(self)
        self.game = catalog_game
        for attr in catalog_game.custom_attributes:
            if attr["key"] == "developerName":
                developer = attr["value"]
                break
        else:
            developer = catalog_game.seller["name"]
        original_price = catalog_game.price.total_price["fmtPrice"]["originalPrice"]
        discount_price = catalog_game.price.total_price["fmtPrice"]["discountPrice"]

        self.ui.title_label.setText(catalog_game.title)
        self.ui.developer_label.setText(developer)
        self.ui.price_label.setText(f'{original_price if original_price != "0" else self.tr("Free")}')
        if original_price != discount_price:
            font = self.ui.price_label.font()
            font.setStrikeOut(True)
            self.ui.price_label.setFont(font)
            self.ui.discount_label.setText(f'{discount_price if discount_price != "0" else self.tr("Free")}')
        else:
            self.ui.discount_label.setVisible(False)
        key_images = catalog_game.key_images
        self.fetchPixmap(
            key_images.for_dimensions(self.width(), self.height()).url
        )

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
        if a0.button() == Qt.RightButton:
            a0.accept()
            dialog = DebugDialog(self.game.__dict__, self)
            dialog.show()
