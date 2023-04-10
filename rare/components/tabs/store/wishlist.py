from typing import List

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QMessageBox, QWidget

from rare.ui.components.tabs.store.wishlist import Ui_Wishlist
from rare.utils.misc import icon
from rare.widgets.side_tab import SideTabContents
from rare.widgets.flow_layout import FlowLayout
from .shop_api_core import ShopApiCore
from .game_widgets import WishlistWidget
from .api.models.response import WishlistItemModel, CatalogOfferModel


class Wishlist(QWidget, SideTabContents):
    show_game_info = pyqtSignal(CatalogOfferModel)
    update_wishlist_signal = pyqtSignal()

    def __init__(self, api_core: ShopApiCore, parent=None):
        super(Wishlist, self).__init__(parent=parent)
        self.implements_scrollarea = True
        self.api_core = api_core
        self.ui = Ui_Wishlist()
        self.ui.setupUi(self)
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

    def update_wishlist(self):
        self.setEnabled(False)
        self.api_core.get_wishlist(self.set_wishlist)

    def delete_from_wishlist(self, game: CatalogOfferModel):
        self.api_core.remove_from_wishlist(
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
        widgets = self.ui.list_container.findChildren(WishlistWidget, options=Qt.FindDirectChildrenOnly)
        for w in widgets:
            self.ui.list_container.layout().removeWidget(w)

        if sort == 0:
            func = lambda x: x.game.title
            reverse = self.ui.reverse.isChecked()
        elif sort == 1:
            func = lambda x: x.game.price.total_price["fmtPrice"]["discountPrice"]
            reverse = self.ui.reverse.isChecked()
        elif sort == 2:
            func = lambda x: x.game.seller["name"]
            reverse = self.ui.reverse.isChecked()
        elif sort == 3:
            func = lambda x: 1 - (x.game.price.total_price["discountPrice"] / x.game.price.total_price["originalPrice"])
            reverse = not self.ui.reverse.isChecked()
        else:
            func = lambda x: x.game.title
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
            w = WishlistWidget(self.api_core.cached_manager, game.offer, self.ui.list_container)
            w.open_game.connect(self.show_game_info)
            w.delete_from_wishlist.connect(self.delete_from_wishlist)
            self.widgets.append(w)
            self.list_layout.addWidget(w)
        self.list_layout.update()
        self.setEnabled(True)
