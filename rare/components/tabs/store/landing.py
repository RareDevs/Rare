import logging
from datetime import datetime, timezone
from typing import List

from PySide6.QtCore import Qt, Slot, Signal, QObject, QEvent
from PySide6.QtGui import QShowEvent, QHideEvent, QResizeEvent
from PySide6.QtWidgets import (
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
from .widgets.details import StoreDetailsWidget
from .widgets.groups import StoreGroup
from .widgets.items import StoreItemWidget

logger = logging.getLogger("StoreLanding")


class LandingPage(SlidingStackedWidget, SideTabContents):

    def __init__(self, store_api: StoreAPI, parent=None):
        super(LandingPage, self).__init__(parent=parent)
        self.implements_scrollarea = True

        self.landing_widget = LandingWidget(store_api, parent=self)
        self.landing_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.landing_widget.set_title.connect(self.set_title)
        self.landing_widget.show_details.connect(self.show_details)

        self.landing_scroll = QScrollArea(self)
        self.landing_scroll.setWidgetResizable(True)
        self.landing_scroll.setFrameStyle(QFrame.Shape.NoFrame | QFrame.Shadow.Plain)
        self.landing_scroll.setWidget(self.landing_widget)
        self.landing_scroll.widget().setAutoFillBackground(False)
        self.landing_scroll.viewport().setAutoFillBackground(False)

        self.details_widget = StoreDetailsWidget([], store_api, parent=self)
        self.details_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.details_widget.set_title.connect(self.set_title)
        self.details_widget.back_clicked.connect(self.show_main)

        self.setDirection(Qt.Orientation.Horizontal)
        self.addWidget(self.landing_scroll)
        self.addWidget(self.details_widget)

    @Slot()
    def show_main(self):
        self.slideInWidget(self.landing_scroll)

    @Slot(object)
    def show_details(self, game: CatalogOfferModel):
        self.details_widget.update_game(game)
        self.slideInWidget(self.details_widget)


class FreeGamesScroll(QScrollArea):
    def __init__(self, parent=None):
        super(FreeGamesScroll, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)

    def setWidget(self, w):
        super().setWidget(w)
        w.installEventFilter(self)

    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        if a0 is self.widget() and a1.type() == QEvent.Type.Resize:
            self.__resize(a0)
            return a0.event(a1)
        return False

    def __resize(self, e: QResizeEvent):
        minh = self.horizontalScrollBar().minimum()
        maxh = self.horizontalScrollBar().maximum()
        # lk: when the scrollbar is not visible, min and max are 0
        if maxh > minh:
            height = (
                e.size().height()
                + self.rect().height() // 2
                - self.contentsRect().height() // 2
                + self.widget().layout().spacing()
                + self.horizontalScrollBar().sizeHint().height()
            )
        else:
            height = e.size().height() + self.rect().height() - self.contentsRect().height()
        self.setMinimumHeight(max(height, self.minimumHeight()))


class LandingWidget(QWidget, SideTabContents):
    show_details = Signal(CatalogOfferModel)

    def __init__(self, api: StoreAPI, parent=None):
        super(LandingWidget, self).__init__(parent=parent)
        self.api = api

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 3, 0)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.free_games_now = StoreGroup(self.tr("Free now"), layout=QHBoxLayout, parent=self)
        self.free_games_now.main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.free_games_now.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.free_games_next = StoreGroup(self.tr("Free next week"), layout=QHBoxLayout, parent=self)
        self.free_games_next.main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.free_games_next.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.discounts_group = StoreGroup(self.tr("Wishlist discounts"), layout=FlowLayout, parent=self)
        self.discounts_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.games_group = StoreGroup(self.tr("Free to play"), FlowLayout, self)
        self.games_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.games_group.loading(False)
        self.games_group.setVisible(False)

        free_scroll = FreeGamesScroll(self)
        free_container = QWidget(free_scroll)
        free_scroll.setWidget(free_container)
        free_container_layout = QHBoxLayout(free_container)

        free_scroll.setWidgetResizable(True)
        free_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        free_scroll.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustToContents)
        free_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        free_container_layout.setContentsMargins(0, 0, 0, 0)
        free_container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        free_container_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)
        free_container_layout.addWidget(self.free_games_now)
        free_container_layout.addWidget(self.free_games_next)

        free_scroll.widget().setAutoFillBackground(False)
        free_scroll.viewport().setAutoFillBackground(False)

        # layout.addWidget(self.free_games_now, alignment=Qt.AlignmentFlag.AlignTop)
        # layout.addWidget(self.free_games_next, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(free_scroll, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.discounts_group, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.games_group, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding))

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
        for w in self.discounts_group.findChildren(StoreItemWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            self.discounts_group.layout().removeWidget(w)
            w.deleteLater()

        for item in filter(lambda x: bool(x.offer.price.totalPrice.discount), wishlist):
            w = StoreItemWidget(self.api.cached_manager, item.offer)
            w.show_details.connect(self.show_details)
            self.discounts_group.layout().addWidget(w)
        have_discounts = any(map(lambda x: bool(x.offer.price.totalPrice.discount), wishlist))
        self.discounts_group.setVisible(have_discounts)
        self.discounts_group.loading(False)

    def __update_free_games(self, free_games: List[CatalogOfferModel]):
        for w in self.free_games_now.findChildren(StoreItemWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            self.free_games_now.layout().removeWidget(w)
            w.deleteLater()

        for w in self.free_games_next.findChildren(StoreItemWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            self.free_games_next.layout().removeWidget(w)
            w.deleteLater()

        date = datetime.now(timezone.utc)
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
        if not data:
            return

        for w in self.games_group.findChildren(StoreItemWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            self.games_group.layout().removeWidget(w)
            w.deleteLater()

        for game in data:
            w = StoreItemWidget(self.api.cached_manager, game)
            w.show_details.connect(self.show_details)
            self.games_group.layout().addWidget(w)
        self.games_group.loading(False)
