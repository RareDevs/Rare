from PySide6.QtGui import QShowEvent, QHideEvent
from legendary.core import LegendaryCore

from rare.widgets.side_tab import SideTabWidget
from .api.models.response import CatalogOfferModel
from .landing import LandingWidget, LandingPage
from .search import SearchPage
from .store_api import StoreAPI
from .wishlist import WishlistPage


class StoreTab(SideTabWidget):

    def __init__(self, core: LegendaryCore, parent=None):
        super(StoreTab, self).__init__(parent=parent)
        self.init = False

        self.core = core
        # self.rcore = RareCore.instance()
        self.api = StoreAPI(
            self.core.egs.session.headers["Authorization"],
            self.core.language_code,
            self.core.country_code,
            []  # [i.asset_infos["Windows"].namespace for i in self.rcore.game_list if bool(i.asset_infos)]
        )

        self.landing = LandingPage(self.api, parent=self)
        self.landing_index = self.addTab(self.landing, self.tr("Store"))

        self.search = SearchPage(self.api, parent=self)
        self.search_index = self.addTab(self.search, self.tr("Search"))

        self.wishlist = WishlistPage(self.api, parent=self)
        self.wishlist_index = self.addTab(self.wishlist, self.tr("Wishlist"))

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous() or self.init:
            return super().showEvent(a0)
        self.init = True
        return super().showEvent(a0)

    def hideEvent(self, a0: QHideEvent) -> None:
        if a0.spontaneous():
            return super().hideEvent(a0)
        # TODO: Implement store unloading
        return super().hideEvent(a0)
