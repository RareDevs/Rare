from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QWidget

from rare.ui.components.tabs.store.wishlist import Ui_Wishlist
from rare.utils.misc import icon
from rare.widgets.side_tab import SideTabContents
from .shop_api_core import ShopApiCore
from .game_widgets import WishlistWidget


class Wishlist(QWidget, Ui_Wishlist, SideTabContents):
    show_game_info = pyqtSignal(dict)
    update_wishlist_signal = pyqtSignal()

    def __init__(self, api_core: ShopApiCore, parent=None):
        super(Wishlist, self).__init__(parent=parent)
        self.api_core = api_core
        self.setupUi(self)
        self.setEnabled(False)
        self.wishlist = []
        self.widgets = []

        self.sort_cb.currentIndexChanged.connect(
            lambda i: self.set_wishlist(self.wishlist, i)
        )
        self.filter_cb.currentIndexChanged.connect(self.set_filter)
        self.reload_button.clicked.connect(self.update_wishlist)
        self.reload_button.setIcon(icon("fa.refresh", color="white"))

        self.reverse.stateChanged.connect(
            lambda: self.set_wishlist(sort=self.sort_cb.currentIndex())
        )

    def update_wishlist(self):
        self.setEnabled(False)
        self.set_title.emit("Wishlist")
        self.api_core.get_wishlist(self.set_wishlist)

    def delete_from_wishlist(self, game):
        self.api_core.remove_from_wishlist(
            game["namespace"],
            game["id"],
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
            self.no_games_label.setVisible(True)
        else:
            self.no_games_label.setVisible(False)

    def set_wishlist(self, wishlist=None, sort=0):
        if wishlist and wishlist[0] == "error":
            return

        if wishlist is not None:
            self.wishlist = wishlist

        for i in self.widgets:
            i.deleteLater()

        if sort == 0:
            sorted_list = sorted(self.wishlist, key=lambda x: x["offer"]["title"])
        elif sort == 1:
            sorted_list = sorted(
                self.wishlist,
                key=lambda x: x["offer"]["price"]["totalPrice"]["fmtPrice"][
                    "discountPrice"
                ],
            )
        elif sort == 2:
            sorted_list = sorted(
                self.wishlist, key=lambda x: x["offer"]["seller"]["name"]
            )
        elif sort == 3:
            sorted_list = sorted(
                self.wishlist,
                reverse=True,
                key=lambda x: 1
                - (
                    x["offer"]["price"]["totalPrice"]["discountPrice"]
                    / x["offer"]["price"]["totalPrice"]["originalPrice"]
                ),
            )
        else:
            sorted_list = self.wishlist
        self.widgets.clear()

        if len(sorted_list) == 0:
            self.no_games_label.setVisible(True)
        else:
            self.no_games_label.setVisible(False)

        if self.reverse.isChecked():
            sorted_list.reverse()

        for game in sorted_list:
            w = WishlistWidget(game["offer"])
            self.widgets.append(w)
            self.list_layout.addWidget(w)
            w.open_game.connect(self.show_game_info.emit)
            w.delete_from_wishlist.connect(self.delete_from_wishlist)
        self.setEnabled(True)
