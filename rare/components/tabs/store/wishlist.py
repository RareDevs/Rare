from enum import IntEnum
from typing import List

from PySide6.QtCore import Signal, Qt, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QMessageBox, QWidget, QSizePolicy

from rare.ui.components.tabs.store.wishlist import Ui_Wishlist
from rare.utils.misc import qta_icon
from rare.widgets.flow_layout import FlowLayout
from rare.widgets.side_tab import SideTabContents
from rare.widgets.sliding_stack import SlidingStackedWidget
from .api.models.response import WishlistItemModel, CatalogOfferModel
from .store_api import StoreAPI
from .widgets.details import StoreDetailsWidget
from .widgets.items import WishlistItemWidget


class WishlistPage(SlidingStackedWidget, SideTabContents):
    def __init__(self, api: StoreAPI, parent=None):
        super(WishlistPage, self).__init__(parent=parent)
        self.implements_scrollarea = True

        self.wishlist_widget = WishlistWidget(api, parent=self)
        self.wishlist_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.wishlist_widget.set_title.connect(self.set_title)
        self.wishlist_widget.show_details.connect(self.show_details)

        self.details_widget = StoreDetailsWidget([], api, parent=self)
        self.details_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.details_widget.set_title.connect(self.set_title)
        self.details_widget.back_clicked.connect(self.show_main)

        self.setDirection(Qt.Orientation.Horizontal)
        self.addWidget(self.wishlist_widget)
        self.addWidget(self.details_widget)

    @Slot()
    def show_main(self):
        self.slideInWidget(self.wishlist_widget)

    @Slot(object)
    def show_details(self, game: CatalogOfferModel):
        self.details_widget.update_game(game)
        self.slideInWidget(self.details_widget)


class WishlistOrder(IntEnum):
    NAME = 1
    PRICE = 2
    DISCOUNT = 3
    DEVELOPER = 4


class WishlistFilter(IntEnum):
    NONE = 0
    DISCOUNT = 1


class WishlistWidget(QWidget, SideTabContents):
    show_details = Signal(CatalogOfferModel)
    update_wishlist = Signal()

    def __init__(self, api: StoreAPI, parent=None):
        super(WishlistWidget, self).__init__(parent=parent)
        self.implements_scrollarea = True
        self.api = api
        self.ui = Ui_Wishlist()
        self.ui.setupUi(self)
        self.ui.main_layout.setContentsMargins(0, 0, 3, 0)

        self.wishlist_layout = FlowLayout()
        self.ui.container_layout.addLayout(self.wishlist_layout, stretch=1)

        filters = {
            WishlistFilter.NONE: self.tr("All items"),
            WishlistFilter.DISCOUNT: self.tr("Discount"),
        }
        for data, text in filters.items():
            self.ui.filter_combo.addItem(text, data)
        self.ui.filter_combo.currentIndexChanged.connect(self.filter_wishlist)

        sortings = {
            WishlistOrder.NAME: self.tr("Name"),
            WishlistOrder.PRICE: self.tr("Price"),
            WishlistOrder.DISCOUNT: self.tr("Discount"),
            WishlistOrder.DEVELOPER: self.tr("Developer"),
        }
        for data, text in sortings.items():
            self.ui.order_combo.addItem(text, data)
        self.ui.order_combo.currentIndexChanged.connect(self.order_wishlist)

        self.ui.reload_button.setIcon(qta_icon("fa.refresh", color="white"))
        self.ui.reload_button.clicked.connect(self.__update_widget)

        self.ui.reverse_check.stateChanged.connect(
            lambda: self.order_wishlist(self.ui.order_combo.currentIndex())
        )

        self.setEnabled(False)

    def showEvent(self, a0: QShowEvent) -> None:
        self.__update_widget()
        return super().showEvent(a0)

    def __update_widget(self):
        self.setEnabled(False)
        self.api.get_wishlist(self.set_wishlist)

    def delete_from_wishlist(self, game: CatalogOfferModel):
        self.api.remove_from_wishlist(
            game.namespace,
            game.id,
            lambda success: self.__update_widget()
            if success
            else QMessageBox.warning(
                self, "Error", self.tr("Could not remove game from wishlist")
            ),
        )
        self.update_wishlist.emit()

    @Slot(int)
    def filter_wishlist(self, index: int = int(WishlistFilter.NONE)):
        list_filter = self.ui.filter_combo.itemData(index, Qt.ItemDataRole.UserRole)
        widgets = self.ui.container.findChildren(WishlistItemWidget, options=Qt.FindChildOption.FindDirectChildrenOnly)
        for w in widgets:
            if list_filter == WishlistFilter.NONE:
                w.setVisible(True)
            elif list_filter == WishlistFilter.DISCOUNT:
                w.setVisible(bool(w.catalog_game.price.totalPrice.discount))
            else:
                w.setVisible(True)
        have_visible = any(map(lambda x: x.isVisible(), widgets))
        self.ui.no_games_label.setVisible(not have_visible)

    @Slot(int)
    def order_wishlist(self, index: int = int(WishlistOrder.NAME)):
        list_order = self.ui.order_combo.itemData(index, Qt.ItemDataRole.UserRole)
        widgets = self.ui.container.findChildren(WishlistItemWidget, options=Qt.FindChildOption.FindDirectChildrenOnly)
        for w in widgets:
            self.wishlist_layout.removeWidget(w)

        if list_order == WishlistOrder.NAME:
            def func(x: WishlistItemWidget):
                return x.catalog_game.title
        elif list_order == WishlistOrder.PRICE:
            def func(x: WishlistItemWidget):
                return x.catalog_game.price.totalPrice.discountPrice
        elif list_order == WishlistOrder.DEVELOPER:
            def func(x: WishlistItemWidget):
                return x.catalog_game.seller["name"]
        elif list_order == WishlistOrder.DISCOUNT:
            def func(x: WishlistItemWidget):
                discount = x.catalog_game.price.totalPrice.discountPrice
                original = x.catalog_game.price.totalPrice.originalPrice
                return 1 - (discount / original)
        else:
            def func(x: WishlistItemWidget):
                return x.catalog_game.title

        reverse = self.ui.reverse_check.isChecked()
        widgets = sorted(widgets, key=func, reverse=reverse)
        for w in widgets:
            self.wishlist_layout.addWidget(w)

    def set_wishlist(self, wishlist: List[WishlistItemModel] = None):
        if wishlist and wishlist[0] == "error":
            return

        widgets = self.ui.container.findChildren(WishlistItemWidget, options=Qt.FindChildOption.FindDirectChildrenOnly)
        for w in widgets:
            self.wishlist_layout.removeWidget(w)
            w.deleteLater()

        self.ui.no_games_label.setVisible(bool(wishlist))

        for game in wishlist:
            w = WishlistItemWidget(self.api.cached_manager, game.offer, self.ui.container)
            w.show_details.connect(self.show_details)
            w.delete_from_wishlist.connect(self.delete_from_wishlist)
            self.wishlist_layout.addWidget(w)

        self.order_wishlist(self.ui.order_combo.currentIndex())
        self.filter_wishlist(self.ui.filter_combo.currentIndex())

        self.setEnabled(True)
