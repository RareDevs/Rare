import logging

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QPushButton

from rare.components.tabs.store.api.models.response import CatalogOfferModel
from rare.models.image import ImageSize
from rare.utils.misc import qta_icon
from rare.utils.qt_requests import QtRequests
from .image import LoadingImageWidget

logger = logging.getLogger("StoreWidgets")


class ItemWidget(LoadingImageWidget):
    show_details = Signal(CatalogOfferModel)

    def __init__(self, manager: QtRequests, catalog_game: CatalogOfferModel = None, parent=None):
        super(ItemWidget, self).__init__(manager, parent=parent)
        self.catalog_game = catalog_game

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.MouseButton.LeftButton:
            a0.accept()
            self.show_details.emit(self.catalog_game)
        if a0.button() == Qt.MouseButton.RightButton:
            a0.accept()


class StoreItemWidget(ItemWidget):
    def __init__(self, manager: QtRequests, catalog_game: CatalogOfferModel = None, parent=None):
        super(StoreItemWidget, self).__init__(manager, catalog_game, parent=parent)
        self.setFixedSize(ImageSize.DisplayWide)
        self.ui.setupUi(self)
        if catalog_game:
            self.init_ui(catalog_game)

    def init_ui(self, game: CatalogOfferModel):
        if not game:
            self.ui.title_label.setText(self.tr("An error occurred"))
            return

        self.ui.title_label.setText(game.title)
        for attr in game.customAttributes:
            if attr["key"] == "developerName":
                developer = attr["value"]
                break
        else:
            developer = game.seller["name"]
        self.ui.developer_label.setText(developer)
        price = game.price.totalPrice.fmtPrice["originalPrice"]
        discount_price = game.price.totalPrice.fmtPrice["discountPrice"]
        self.ui.price_label.setText(f'{price if price != "0" else self.tr("Free")}')
        if price != discount_price:
            font = self.ui.price_label.font()
            font.setStrikeOut(True)
            self.ui.price_label.setFont(font)
            self.ui.discount_label.setText(f'{discount_price if discount_price != "0" else self.tr("Free")}')
        else:
            self.ui.discount_label.setVisible(False)

        key_images = game.keyImages
        self.fetchPixmap(key_images.for_dimensions(self.width(), self.height()).url)

        # for img in json_info["keyImages"]:
        #     if img["type"] in ["DieselStoreFrontWide", "OfferImageWide", "VaultClosed", "ProductLogo"]:
        #         if img["type"] == "VaultClosed" and json_info["title"] != "Mystery Game":
        #             continue
        #         self.fetchPixmap(img["url"])
        #         break
        # else:
        #     logger.info(", ".join([img["type"] for img in json_info["keyImages"]]))


class SearchItemWidget(ItemWidget):
    def __init__(self, manager: QtRequests, catalog_game: CatalogOfferModel, parent=None):
        super(SearchItemWidget, self).__init__(manager, catalog_game, parent=parent)
        self.setFixedSize(ImageSize.LibraryTall)
        self.ui.setupUi(self)

        key_images = catalog_game.keyImages
        self.fetchPixmap(key_images.for_dimensions(self.width(), self.height()).url)

        self.ui.title_label.setText(catalog_game.title)

        price = catalog_game.price.totalPrice.fmtPrice["originalPrice"]
        discount_price = catalog_game.price.totalPrice.fmtPrice["discountPrice"]
        self.ui.price_label.setText(f'{price if price != "0" else self.tr("Free")}')
        if price != discount_price:
            font = self.ui.price_label.font()
            font.setStrikeOut(True)
            self.ui.price_label.setFont(font)
            self.ui.discount_label.setText(f'{discount_price if discount_price != "0" else self.tr("Free")}')
        else:
            self.ui.discount_label.setVisible(False)


class WishlistItemWidget(ItemWidget):
    delete_from_wishlist = Signal(CatalogOfferModel)

    def __init__(self, manager: QtRequests, catalog_game: CatalogOfferModel, parent=None):
        super(WishlistItemWidget, self).__init__(manager, catalog_game, parent=parent)
        self.setFixedSize(ImageSize.DisplayWide)
        self.ui.setupUi(self)
        for attr in catalog_game.customAttributes:
            if attr["key"] == "developerName":
                developer = attr["value"]
                break
        else:
            developer = catalog_game.seller["name"]
        original_price = catalog_game.price.totalPrice.fmtPrice["originalPrice"]
        discount_price = catalog_game.price.totalPrice.fmtPrice["discountPrice"]

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
        key_images = catalog_game.keyImages
        self.fetchPixmap(
            key_images.for_dimensions(self.width(), self.height()).url
        )

        self.delete_button = QPushButton(self)
        self.delete_button.setIcon(qta_icon("mdi.delete", color="white"))
        self.delete_button.clicked.connect(
            lambda: self.delete_from_wishlist.emit(self.catalog_game)
        )
        self.layout().insertWidget(0, self.delete_button, alignment=Qt.AlignmentFlag.AlignRight)

