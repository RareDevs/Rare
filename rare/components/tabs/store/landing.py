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

from rare.components.tabs.store.api.models.response import CatalogOfferModel, WishlistItemModel
from rare.widgets.flow_layout import FlowLayout
from rare.widgets.side_tab import SideTabContents
from rare.widgets.sliding_stack import SlidingStackedWidget
from .store_api import StoreAPI
from .widgets.details import DetailsWidget
from .widgets.groups import StoreGroup
from .widgets.items import StoreItemWidget

logger = logging.getLogger("StoreLanding")


class LandingPage(SlidingStackedWidget, SideTabContents):

    def __init__(self, store_api: StoreAPI, parent=None):
        super(LandingPage, self).__init__(parent=parent)
        self.implements_scrollarea = True

        self.landing_widget = LandingWidget(store_api, parent=self)
        self.landing_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.landing_widget.set_title.connect(self.set_title)
        self.landing_widget.show_details.connect(self.show_details)

        self.landing_scroll = QScrollArea(self)
        self.landing_scroll.setWidgetResizable(True)
        self.landing_scroll.setFrameStyle(QFrame.NoFrame | QFrame.Plain)
        self.landing_scroll.setWidget(self.landing_widget)

        self.details_widget = DetailsWidget([], store_api, parent=self)
        self.details_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.details_widget.set_title.connect(self.set_title)
        self.details_widget.back_clicked.connect(self.show_main)

        self.setDirection(Qt.Horizontal)
        self.addWidget(self.landing_scroll)
        self.addWidget(self.details_widget)

    @pyqtSlot()
    def show_main(self):
        self.slideInWidget(self.landing_scroll)

    @pyqtSlot(object)
    def show_details(self, game: CatalogOfferModel):
        self.details_widget.update_game(game)
        self.slideInWidget(self.details_widget)


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

        self.games_group = StoreGroup(self.tr("Free to play"), FlowLayout, self)
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
        self.api.get_free(self.__update_free_games)
        self.api.get_wishlist(self.__update_wishlist_discounts)
        return super().showEvent(a0)

    def hideEvent(self, a0: QHideEvent) -> None:
        if a0.spontaneous():
            return super().hideEvent(a0)
        # TODO: Implement tab unloading
        return super().hideEvent(a0)

    def __update_wishlist_discounts(self, wishlist: List[WishlistItemModel]):
        for w in self.discounts_group.findChildren(StoreItemWidget, options=Qt.FindDirectChildrenOnly):
            self.discounts_group.layout().removeWidget(w)
            w.deleteLater()

        for item in wishlist:
            if item.offer.price.totalPrice.discount > 0:
                w = StoreItemWidget(self.api.cached_manager, item.offer)
                w.show_details.connect(self.show_details)
                self.discounts_group.layout().addWidget(w)
        self.discounts_group.setVisible(bool(wishlist))
        self.discounts_group.loading(False)

    def __update_free_games(self, free_games: List[CatalogOfferModel]):
        for w in self.free_games_now.findChildren(StoreItemWidget, options=Qt.FindDirectChildrenOnly):
            self.free_games_now.layout().removeWidget(w)
            w.deleteLater()

        for w in self.free_games_next.findChildren(StoreItemWidget, options=Qt.FindDirectChildrenOnly):
            self.free_games_next.layout().removeWidget(w)
            w.deleteLater()

        date = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        free_now = []
        free_next = []
        for item in free_games:
            try:
                if item.price.totalPrice.discountPrice == 0:
                    free_now.append(item)
                    continue
                if item.title == "Mystery Game":
                    free_next.append(item)
                    continue
            except KeyError as e:
                logger.warning(str(e))

            if item.promotions is not None:
                if not item.promotions.promotionalOffers:
                    start_date = item.promotions.upcomingPromotionalOffers[0].promotionalOffers[0].startDate
                else:
                    start_date = item.promotions.promotionalOffers[0].promotionalOffers[0].startDate

                if start_date > date:
                    free_next.append(item)

        # free games now
        self.free_games_now.setVisible(bool(free_now))
        for item in free_now:
            w = StoreItemWidget(self.api.cached_manager, item)
            w.show_details.connect(self.show_details)
            self.free_games_now.layout().addWidget(w)
        self.free_games_now.loading(False)

        # free games next week
        self.free_games_next.setVisible(bool(free_next))
        for item in free_next:
            w = StoreItemWidget(self.api.cached_manager, item)
            if item.title != "Mystery Game":
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
