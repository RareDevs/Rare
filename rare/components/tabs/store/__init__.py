from PySide6.QtCore import Signal
from PySide6.QtGui import QHideEvent, QShowEvent

from rare.lgndr.core import LegendaryCore
from rare.shared import RareCore
from rare.widgets.side_tab import SideTabWidget

from .landing import LandingPage
from .store_api import StoreAPI
from .wishlist import WishlistPage


class StoreTab(SideTabWidget):
    open_library = Signal()

    def __init__(self, core: LegendaryCore, rcore: RareCore | None = None, parent=None):
        super(StoreTab, self).__init__(parent=parent)
        self.init = False

        self.core = core
        self.rcore = rcore
        self.api = StoreAPI(
            self.core.egs.session.headers['Authorization'],
            self.core.language_code,
            self.core.country_code,
            [],
            self.core.egs._store_user_agent,
        )

        self.landing = LandingPage(self.api, self.rcore, parent=self)
        self.landing_index = self.addTab(self.landing, self.tr('Store'))

        self.wishlist = WishlistPage(self.api, self.rcore, parent=self)
        self.wishlist_index = self.addTab(self.wishlist, self.tr('Wishlist'))

        # forward library navigation requests from the details pages
        self.landing.open_library.connect(self.open_library)
        self.wishlist.open_library.connect(self.open_library)

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
