import datetime
import logging
from typing import List

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QShowEvent, QHideEvent
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QVBoxLayout,
    QSpacerItem,
    QScrollArea,
    QFrame,
)

from rare.widgets.flow_layout import FlowLayout
from rare.widgets.side_tab import SideTabContents
from rare.widgets.sliding_stack import SlidingStackedWidget
from rare.components.tabs.store.api.models.response import CatalogOfferModel, WishlistItemModel
from .api.models.utils import parse_date
from .store_api import StoreAPI
from .widgets.details import DetailsWidget
from .widgets.items import StoreItemWidget
from .widgets.groups import StoreGroup

logger = logging.getLogger("StoreLanding")


class LandingPage(SlidingStackedWidget, SideTabContents):

    def __init__(self, api: StoreAPI, parent=None):
        super(LandingPage, self).__init__(parent=parent)
        self.implements_scrollarea = True

        self.landing_widget = LandingWidget(api, parent=self)
        self.landing_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.landing_widget.set_title.connect(self.set_title)
        self.landing_widget.show_details.connect(self.show_details)

        self.landing_scroll = QScrollArea(self)
        self.landing_scroll.setWidgetResizable(True)
        self.landing_scroll.setFrameStyle(QFrame.NoFrame | QFrame.Plain)
        self.landing_scroll.setWidget(self.landing_widget)

        self.details_widget = DetailsWidget([], api, parent=self)
        self.details_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.details_widget.set_title.connect(self.set_title)
        self.details_widget.back_clicked.connect(self.show_main)

        self.details_scroll = QScrollArea(self)
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFrameStyle(QFrame.NoFrame | QFrame.Plain)
        self.details_scroll.setWidget(self.details_widget)

        self.setDirection(Qt.Horizontal)
        self.addWidget(self.landing_scroll)
        self.addWidget(self.details_scroll)

    @pyqtSlot()
    def show_main(self):
        self.slideInWidget(self.landing_scroll)

    @pyqtSlot(object)
    def show_details(self, game: CatalogOfferModel):
        self.details_widget.update_game(game)
        self.slideInWidget(self.details_scroll)


class LandingWidget(QWidget, SideTabContents):
    show_details = pyqtSignal(CatalogOfferModel)

    def __init__(self, api: StoreAPI, parent=None):
        super(LandingWidget, self).__init__(parent=parent)
        self.api = api

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 3, 0)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.free_games_now = StoreGroup(self.tr("Free now"), layout=QHBoxLayout, parent=self)
        self.free_games_now.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.free_games_next = StoreGroup(self.tr("Free next week"), layout=QHBoxLayout, parent=self)
        self.free_games_next.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.discounts_group = StoreGroup(self.tr("Wishlist discounts"), layout=FlowLayout, parent=self)
        self.discounts_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.games_group = StoreGroup(self.tr("Games"), FlowLayout, self)
        self.games_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.games_group.loading(False)
        self.games_group.setVisible(True)

        layout.addWidget(self.free_games_now, alignment=Qt.AlignTop)
        layout.addWidget(self.free_games_next, alignment=Qt.AlignTop)
        layout.addWidget(self.discounts_group, alignment=Qt.AlignTop)
        layout.addWidget(self.games_group, alignment=Qt.AlignTop)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Fixed, QSizePolicy.Expanding))

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)
        self.api.get_free_games(self.__add_free)
        self.api.get_wishlist(self.__add_discounts)
        return super().showEvent(a0)

    def hideEvent(self, a0: QHideEvent) -> None:
        if a0.spontaneous():
            return super().hideEvent(a0)
        # TODO: Implement tab unloading
        return super().hideEvent(a0)

    def __add_discounts(self, wishlist: List[WishlistItemModel]):
        for w in self.discounts_group.findChildren(StoreItemWidget, options=Qt.FindDirectChildrenOnly):
            self.discounts_group.layout().removeWidget(w)
            w.deleteLater()

        discounts = 0
        for game in wishlist:
            if not game:
                continue
            try:
                if game.offer.price.total_price["discount"] > 0:
                    w = StoreItemWidget(self.api.cached_manager, game.offer)
                    w.show_details.connect(self.show_details)
                    self.discounts_group.layout().addWidget(w)
                    discounts += 1
            except Exception as e:
                logger.warning(f"{game} {e}")
                continue
        # self.discounts_group.setVisible(discounts > 0)
        self.discounts_group.loading(False)

    def __add_free(self, free_games: List[CatalogOfferModel]):
        for w in self.free_games_now.findChildren(StoreItemWidget, options=Qt.FindDirectChildrenOnly):
            self.free_games_now.layout().removeWidget(w)
            w.deleteLater()

        for w in self.free_games_next.findChildren(StoreItemWidget, options=Qt.FindDirectChildrenOnly):
            self.free_games_next.layout().removeWidget(w)
            w.deleteLater()

        date = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        free_now = []
        free_next = []
        for game in free_games:
            try:
                if (
                    game.price.total_price["fmtPrice"]["discountPrice"] == "0"
                    and game.price.total_price["fmtPrice"]["originalPrice"]
                    != game.price.total_price["fmtPrice"]["discountPrice"]
                ):
                    free_now.append(game)
                    continue

                if game.title == "Mystery Game":
                    free_next.append(game)
                    continue
            except KeyError as e:
                logger.warning(str(e))

            try:
                # parse datetime to check if game is next week or now
                try:
                    start_date = parse_date(
                        game.promotions["upcomingPromotionalOffers"][0]["promotionalOffers"][0]["startDate"]
                    )
                except Exception:
                    try:
                        start_date = parse_date(
                            game.promotions["promotionalOffers"][0]["promotionalOffers"][0]["startDate"]
                        )
                    except Exception as e:
                        continue

            except TypeError:
                print("type error")
                continue

            if start_date > date:
                free_next.append(game)

        # free games now
        self.free_games_now.setVisible(bool(len(free_now)))
        for game in free_now:
            w = StoreItemWidget(self.api.cached_manager, game)
            w.show_details.connect(self.show_details)
            self.free_games_now.layout().addWidget(w)
        self.free_games_now.loading(False)

        # free games next week
        self.free_games_next.setVisible(bool(len(free_next)))
        for game in free_next:
            w = StoreItemWidget(self.api.cached_manager, game)
            if game.title != "Mystery Game":
                w.show_details.connect(self.show_details)
            self.free_games_next.layout().addWidget(w)
        self.free_games_next.loading(False)

    def show_games(self, data):
        for w in self.games_group.findChildren(StoreItemWidget, options=Qt.FindDirectChildrenOnly):
            self.games_group.layout().removeWidget(w)
            w.deleteLater()

        if data:
            for game in data:
                w = StoreItemWidget(self.api.cached_manager, game)
                w.show_details.connect(self.show_details)
                self.games_group.layout().addWidget(w)
        self.games_group.loading(False)
