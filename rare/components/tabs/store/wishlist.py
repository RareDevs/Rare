from enum import IntEnum
from typing import List

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QMessageBox, QSizePolicy, QWidget

from rare.ui.components.tabs.store.wishlist import Ui_Wishlist
from rare.utils.misc import qta_icon
from rare.widgets.flow_layout import FlowLayout
from rare.widgets.side_tab import SideTabContents
from rare.widgets.sliding_stack import SlidingStackedWidget

from .api.models.response import CatalogOfferModel, WishlistItemModel
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

        self.ui.reload_button.setIcon(qta_icon("fa.refresh", "fa5s.sync", color="white"))
        self.ui.reload_button.clicked.connect(self._update_widget)

        self.ui.reverse_check.stateChanged.connect(self._on_reverse_changed)

        self.setEnabled(False)

    def showEvent(self, a0: QShowEvent) -> None:
        self._update_widget()
        return super().showEvent(a0)

    def _update_widget(self):
        self.setEnabled(False)
        self.api.get_wishlist(self.set_wishlist)

    def delete_from_wishlist(self, game: CatalogOfferModel):
        self.api.remove_from_wishlist(
            game.namespace,
            game.id,
            lambda success: self._update_widget()
            if success
            else QMessageBox.warning(self, "Error", self.tr("Could not remove game from wishlist")),
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

    __ordering = {
        WishlistOrder.NAME: lambda x: x.catalog_game.title,
        WishlistOrder.PRICE: lambda x: x.catalog_game.price.totalPrice.discountPrice,
        WishlistOrder.DEVELOPER: lambda x: x.catalog_game.seller["name"],
        WishlistOrder.DISCOUNT: lambda x: 1 - (x.catalog_game.price.totalPrice.discountPrice / x.catalog_game.price.totalPrice.originalPrice)
    }

    @Slot(int)
    def order_wishlist(self, index: int = int(WishlistOrder.NAME)):
        list_order = self.ui.order_combo.itemData(index, Qt.ItemDataRole.UserRole)
        widgets = self.ui.container.findChildren(WishlistItemWidget, options=Qt.FindChildOption.FindDirectChildrenOnly)
        for w in widgets:
            self.wishlist_layout.removeWidget(w)

        reverse = self.ui.reverse_check.isChecked()
        widgets = sorted(widgets, key=self.__ordering[list_order], reverse=reverse)
        for w in widgets:
            self.wishlist_layout.addWidget(w)

    @Slot(Qt.CheckState)
    def _on_reverse_changed(self, state: Qt.CheckState):
        self.order_wishlist(self.ui.order_combo.currentIndex())

    @Slot(object)
    def set_wishlist(self, wishlist: List[WishlistItemModel] = None):
        if wishlist and wishlist[0] == "error":
            return

        widgets = self.ui.container.findChildren(WishlistItemWidget, options=Qt.FindChildOption.FindDirectChildrenOnly)
        for w in widgets:
            self.wishlist_layout.removeWidget(w)
            w.disconnect(w)
            w.deleteLater()

        self.ui.no_games_label.setVisible(bool(wishlist))

        widgets = []
        for game in wishlist:
            w = WishlistItemWidget(self.api.cached_manager, game.offer, self.ui.container)
            w.show_details.connect(self.show_details)
            w.delete_from_wishlist.connect(self.delete_from_wishlist)
            widgets.append(w)

        list_order = self.ui.order_combo.currentData(Qt.ItemDataRole.UserRole)
        reverse = self.ui.reverse_check.isChecked()
        widgets = sorted(widgets, key=self.__ordering[list_order], reverse=reverse)
        for w in widgets:
            self.wishlist_layout.addWidget(w)

        self.filter_wishlist(self.ui.filter_combo.currentIndex())

        self.setEnabled(True)
