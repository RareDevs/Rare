from typing import List

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QMessageBox, QWidget, QScrollArea, QFrame, QSizePolicy

from rare.ui.components.tabs.store.wishlist import Ui_Wishlist
from rare.utils.misc import icon
from rare.widgets.flow_layout import FlowLayout
from rare.widgets.side_tab import SideTabContents
from rare.widgets.sliding_stack import SlidingStackedWidget
from .api.models.response import WishlistItemModel, CatalogOfferModel
from .store_api import StoreAPI
from .widgets.details import DetailsWidget
from .widgets.items import WishlistItemWidget


class WishlistPage(SlidingStackedWidget, SideTabContents):
    def __init__(self, api: StoreAPI, parent=None):
        super(WishlistPage, self).__init__(parent=parent)
        self.implements_scrollarea = True

        self.wishlist_widget = WishlistWidget(api, parent=self)
        self.wishlist_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.wishlist_widget.set_title.connect(self.set_title)
        self.wishlist_widget.show_details.connect(self.show_details)

        self.details_widget = DetailsWidget([], api, parent=self)
        self.details_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.details_widget.set_title.connect(self.set_title)
        self.details_widget.back_clicked.connect(self.show_main)

        self.setDirection(Qt.Horizontal)
        self.addWidget(self.wishlist_widget)
        self.addWidget(self.details_widget)

    @pyqtSlot()
    def show_main(self):
        self.slideInWidget(self.wishlist_widget)

    @pyqtSlot(object)
    def show_details(self, game: CatalogOfferModel):
        self.details_widget.update_game(game)
        self.slideInWidget(self.details_widget)


class WishlistWidget(QWidget, SideTabContents):
    show_details = pyqtSignal(CatalogOfferModel)
    update_wishlist_signal = pyqtSignal()

    def __init__(self, api: StoreAPI, parent=None):
        super(WishlistWidget, self).__init__(parent=parent)
        self.implements_scrollarea = True
        self.api = api
        self.ui = Ui_Wishlist()
        self.ui.setupUi(self)
        self.ui.main_layout.setContentsMargins(0, 0, 3, 0)
        self.setEnabled(False)
        self.wishlist = []
        self.widgets = []

        self.list_layout = FlowLayout(self.ui.list_container)

        self.ui.sort_cb.currentIndexChanged.connect(self.sort_wishlist)
        self.ui.filter_cb.currentIndexChanged.connect(self.set_filter)
        self.ui.reload_button.clicked.connect(self.update_wishlist)
        self.ui.reload_button.setIcon(icon("fa.refresh", color="white"))

        self.ui.reverse.stateChanged.connect(
            lambda: self.sort_wishlist(sort=self.ui.sort_cb.currentIndex())
        )

    def showEvent(self, a0: QShowEvent) -> None:
        self.update_wishlist()
        return super().showEvent(a0)

    def update_wishlist(self):
        self.setEnabled(False)
        self.api.get_wishlist(self.set_wishlist)

    def delete_from_wishlist(self, game: CatalogOfferModel):
        self.api.remove_from_wishlist(
            game.namespace,
            game.id,
            lambda success: self.update_wishlist()
            if success
            else QMessageBox.warning(
                self, "Error", self.tr("Could not remove game from wishlist")
            ),
        )
        self.update_wishlist_signal.emit()

    def set_filter(self, i):
        count = 0
        for w in self.widgets:
            if i == 1 and not w.discount:
                w.setVisible(False)
            else:
                w.setVisible(True)
                count += 1

            if i == 0:
                w.setVisible(True)

        if count == 0:
            self.ui.no_games_label.setVisible(True)
        else:
            self.ui.no_games_label.setVisible(False)

    def sort_wishlist(self, sort=0):
        widgets = self.ui.list_container.findChildren(WishlistItemWidget, options=Qt.FindDirectChildrenOnly)
        for w in widgets:
            self.ui.list_container.layout().removeWidget(w)

        if sort == 0:
            func = lambda x: x.catalog_game.title
            reverse = self.ui.reverse.isChecked()
        elif sort == 1:
            func = lambda x: x.catalog_game.price.totalPrice["fmtPrice"]["discountPrice"]
            reverse = self.ui.reverse.isChecked()
        elif sort == 2:
            func = lambda x: x.catalog_game.seller["name"]
            reverse = self.ui.reverse.isChecked()
        elif sort == 3:
            func = lambda x: 1 - (x.catalog_game.price.totalPrice["discountPrice"] / x.catalog_game.price.totalPrice["originalPrice"])
            reverse = not self.ui.reverse.isChecked()
        else:
            func = lambda x: x.catalog_game.title
            reverse = self.ui.reverse.isChecked()

        widgets = sorted(widgets, key=func, reverse=reverse)
        for w in widgets:
            self.ui.list_container.layout().addWidget(w)

    def set_wishlist(self, wishlist: List[WishlistItemModel] = None, sort=0):
        if wishlist and wishlist[0] == "error":
            return

        if wishlist is not None:
            self.wishlist = wishlist

        for i in self.widgets:
            i.deleteLater()

        self.widgets.clear()

        if len(wishlist) == 0:
            self.ui.no_games_label.setVisible(True)
        else:
            self.ui.no_games_label.setVisible(False)

        for game in wishlist:
            w = WishlistItemWidget(self.api.cached_manager, game.offer, self.ui.list_container)
            w.show_details.connect(self.show_details)
            w.delete_from_wishlist.connect(self.delete_from_wishlist)
            self.widgets.append(w)
            self.list_layout.addWidget(w)
        self.list_layout.update()
        self.setEnabled(True)
