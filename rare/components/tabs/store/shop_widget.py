import datetime
import logging
from typing import List

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QGroupBox,
    QCheckBox,
    QLabel,
    QHBoxLayout,
    QWidget, QSizePolicy, QScrollArea, QVBoxLayout, QFrame, QSpacerItem,
)
from legendary.core import LegendaryCore

from rare.ui.components.tabs.store.store import Ui_ShopWidget
from rare.utils.extra_widgets import ButtonLineEdit
from rare.widgets.flow_layout import FlowLayout
from rare.widgets.side_tab import SideTabContents
from rare.widgets.sliding_stack import SlidingStackedWidget
from .store_widgets import ShopGroupBox
from .api.models.query import SearchStoreQuery
from .api.models.response import CatalogOfferModel, WishlistItemModel
from .api.models.utils import parse_date
from .constants import Constants
from .game_widgets import GameWidget
from .search_results import SearchResults
from .shop_api_core import ShopApiCore

logger = logging.getLogger("Shop")


# noinspection PyAttributeOutsideInit,PyBroadException
class ShopWidget(QWidget, SideTabContents):
    show_info = pyqtSignal(str)
    show_game = pyqtSignal(dict)

    def __init__(self, cache_dir, core: LegendaryCore, shop_api: ShopApiCore, parent=None):
        super(ShopWidget, self).__init__(parent=parent)
        self.implements_scrollarea = True
        self.ui = Ui_ShopWidget()
        self.ui.setupUi(self)
        self.cache_dir = cache_dir
        self.core = core
        self.api_core = shop_api
        self.price = ""
        self.tags = []
        self.types = []
        self.update_games_allowed = True

        self.free_game_widgets = []
        self.active_search_request = False
        self.next_search = ""
        self.wishlist: List = []

        self.browse_scrollarea = QScrollArea(self)
        self.browse_scrollarea.setWidgetResizable(True)
        self.browse_scrollarea.setFrameStyle(QFrame.NoFrame | QFrame.Plain)
        self.browse_container = QWidget(self.browse_scrollarea)
        browse_contailer_layout = QVBoxLayout(self.browse_container)
        browse_contailer_layout.setContentsMargins(0, 0, 3, 0)
        self.browse_container.setLayout(browse_contailer_layout)
        self.browse_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.browse_scrollarea.setWidget(self.browse_container)

        # self.free_scrollarea = QScrollArea(self.browse_container)
        # self.free_scrollarea.setWidgetResizable(True)
        # self.free_scrollarea.setFrameStyle(QFrame.NoFrame | QFrame.Plain)
        # self.free_container = QWidget(self.free_scrollarea)
        # free_container_layout = QHBoxLayout(self.free_container)
        # free_container_layout.setContentsMargins(0, 0, 0, 3)
        # self.free_container.setLayout(free_container_layout)
        # self.free_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.free_scrollarea.setWidget(self.free_container)
        #
        # self.browse_container.layout().addWidget(self.free_scrollarea)

        self.discounts_group = ShopGroupBox(self.tr("Discounts from your wishlist"), FlowLayout, self)
        self.browse_container.layout().addWidget(self.discounts_group)
        self.discounts_group.loading(True)

        self.games_group = ShopGroupBox(self.tr("Games"), FlowLayout, self)
        self.browse_container.layout().addWidget(self.games_group)
        self.games_group.loading(True)
        self.games_group.setVisible(False)

        self.browse_container.layout().addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.search_scrollarea = SearchResults(self.api_core, self)

        self.search_bar = ButtonLineEdit(
            "fa.search", placeholder_text=self.tr("Search Games")
        )
        self.ui.left_layout.addWidget(self.search_bar)

        self.browse_stack = SlidingStackedWidget(self)
        self.browse_stack.setDirection(Qt.Vertical)
        self.browse_stack.addWidget(self.browse_scrollarea)
        self.browse_stack.addWidget(self.search_scrollarea)
        self.ui.left_layout.addWidget(self.browse_stack)

        # self.search_bar.textChanged.connect(self.search_games)

        self.search_bar.returnPressed.connect(self.show_search_results)
        self.search_bar.buttonClicked.connect(self.show_search_results)

        self.init_filter()

        # self.search_bar.textChanged.connect(self.load_completer)

    def load(self):
        # load free games
        self.api_core.get_free_games(self.add_free_games)
        # load wishlist
        self.api_core.get_wishlist(self.add_wishlist_items)
        # load browse games
        self.prepare_request()

    def update_wishlist(self):
        self.api_core.get_wishlist(self.add_wishlist_items)

    def add_wishlist_items(self, wishlist: List[WishlistItemModel]):
        for w in self.discounts_group.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            self.discounts_group.layout().removeWidget(w)
            w.deleteLater()

        # if wishlist and wishlist[0] == "error":
        #     self.discounts_group.layout().addWidget(
        #         QLabel(self.tr("Failed to get wishlist: {}").format(wishlist[1]))
        #     )
        #     btn = QPushButton(self.tr("Reload"))
        #     self.discount_widget.layout().addWidget(btn)
        #     btn.clicked.connect(
        #         lambda: self.api_core.get_wishlist(self.add_wishlist_items)
        #     )
        #     self.discount_stack.setCurrentIndex(0)
        #     return

        discounts = 0
        for game in wishlist:
            if not game:
                continue
            try:
                if game.offer.price.total_price["discount"] > 0:
                    w = GameWidget(self.api_core.cached_manager, game.offer)
                    w.show_info.connect(self.show_game)
                    self.discounts_group.layout().addWidget(w)
                    discounts += 1
            except Exception as e:
                logger.warning(f"{game} {e}")
                continue
        self.discounts_group.setVisible(discounts > 0)
        self.discounts_group.loading(False)
        # FIXME: FlowLayout doesn't update on adding widget
        self.discounts_group.layout().update()

    def add_free_games(self, free_games: List[CatalogOfferModel]):
        for w in self.browse_container.layout().findChildren(QGroupBox, options=Qt.FindDirectChildrenOnly):
            self.browse_container.layout().removeWidget(w)
            w.deleteLater()

        # if free_games and free_games[0] == "error":
        #     self.ui.free_container.layout().addWidget(
        #         QLabel(self.tr("Failed to fetch free games: {}").format(free_games[1]))
        #     )
        #     btn = QPushButton(self.tr("Reload"))
        #     self.ui.free_container.layout().addWidget(btn)
        #     btn.clicked.connect(
        #         lambda: self.api_core.get_free_games(self.add_free_games)
        #     )
        #     self.ui.free_container.setEnabled(True)
        #     return

        free_games_now = ShopGroupBox(self.tr("Free now"), layouting=QHBoxLayout, parent=self.browse_container)
        free_games_now.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.free_games_now.setLayout(free_games_now_layout)
        self.browse_container.layout().insertWidget(0, free_games_now)

        free_games_next = ShopGroupBox(self.tr("Free next week"), layouting=QHBoxLayout, parent=self.browse_container)
        free_games_next.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.free_games_next.setLayout(free_games_next_layout)
        self.browse_container.layout().insertWidget(1, free_games_next)

        date = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        free_now_list = []
        free_next_list = []
        for game in free_games:
            try:
                if (
                    game.price.total_price["fmtPrice"]["discountPrice"] == "0"
                    and game.price.total_price["fmtPrice"]["originalPrice"]
                    != game.price.total_price["fmtPrice"]["discountPrice"]
                ):
                    free_now_list.append(game)
                    continue

                if game.title == "Mystery Game":
                    free_next_list.append(game)
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
                free_next_list.append(game)
        # free games now
        now_free = 0
        for free_game in free_now_list:
            w = GameWidget(self.api_core.cached_manager, free_game)
            w.show_info.connect(self.show_game)
            free_games_now.layout().addWidget(w)
            # self.free_game_widgets.append(w)
            now_free += 1
        if now_free == 0:
            free_games_now.layout().addWidget(
                QLabel(self.tr("Could not find current free game"))
            )
        free_games_now.loading(False)

        # free games next week
        for free_game in free_next_list:
            w = GameWidget(self.api_core.cached_manager, free_game)
            if free_game.title != "Mystery Game":
                w.show_info.connect(self.show_game)
            free_games_next.layout().addWidget(w)
        free_games_next.loading(False)
        # self.coming_free_games.setFixedWidth(int(40 + len(coming_free_games) * 300))

        # self.free_scrollarea.setMinimumHeight(
        #     free_games_now.sizeHint().height()
        #     + self.free_container.layout().contentsMargins().top()
        #     + self.free_container.layout().contentsMargins().bottom()
        #     + self.free_scrollarea.horizontalScrollBar().sizeHint().height()
        # )
        # self.free_scrollarea.setEnabled(True)

    def show_search_results(self):
        if self.search_bar.text():
            self.browse_stack.slideInWidget(self.search_scrollarea)
            self.search_scrollarea.load_results(self.search_bar.text())
            # self.show_info.emit(self.search_bar.text())

    def init_filter(self):
        self.ui.none_price.toggled.connect(
            lambda: self.prepare_request("") if self.ui.none_price.isChecked() else None
        )
        self.ui.free_button.toggled.connect(
            lambda: self.prepare_request("free")
            if self.ui.free_button.isChecked()
            else None
        )
        self.ui.under10.toggled.connect(
            lambda: self.prepare_request("<price>[0, 1000)")
            if self.ui.under10.isChecked()
            else None
        )
        self.ui.under20.toggled.connect(
            lambda: self.prepare_request("<price>[0, 2000)")
            if self.ui.under20.isChecked()
            else None
        )
        self.ui.under30.toggled.connect(
            lambda: self.prepare_request("<price>[0, 3000)")
            if self.ui.under30.isChecked()
            else None
        )
        self.ui.above.toggled.connect(
            lambda: self.prepare_request("<price>[1499,]")
            if self.ui.above.isChecked()
            else None
        )
        # self.on_discount.toggled.connect(lambda: self.prepare_request("sale") if self.on_discount.isChecked() else None)
        self.ui.on_discount.toggled.connect(lambda: self.prepare_request())
        constants = Constants()

        self.checkboxes = []

        for groupbox, variables in [
            (self.ui.genre_group, constants.categories),
            (self.ui.platform_group, constants.platforms),
            (self.ui.others_group, constants.others),
            (self.ui.type_group, constants.types),
        ]:

            for text, tag in variables:
                checkbox = CheckBox(text, tag)
                checkbox.activated.connect(lambda x: self.prepare_request(added_tag=x))
                checkbox.deactivated.connect(
                    lambda x: self.prepare_request(removed_tag=x)
                )
                groupbox.layout().addWidget(checkbox)
                self.checkboxes.append(checkbox)
        self.ui.reset_button.clicked.connect(self.reset_filters)
        self.ui.filter_scrollarea.setMinimumWidth(
            self.ui.filter_container.sizeHint().width()
            + self.ui.filter_container.layout().contentsMargins().left()
            + self.ui.filter_container.layout().contentsMargins().right()
            + self.ui.filter_scrollarea.verticalScrollBar().sizeHint().width()
        )

    def reset_filters(self):
        self.browse_stack.slideInWidget(self.browse_scrollarea)
        self.update_games_allowed = False
        for cb in self.checkboxes:
            cb.setChecked(False)
        self.ui.none_price.setChecked(True)

        self.tags = []
        self.types = []
        self.update_games_allowed = True
        self.prepare_request("")

        self.ui.on_discount.setChecked(False)

    def prepare_request(
        self,
        price: str = None,
        added_tag: int = 0,
        removed_tag: int = 0,
        added_type: str = "",
        removed_type: str = "",
    ):
        if not self.update_games_allowed:
            return
        if price is not None:
            self.price = price

        if added_tag != 0:
            self.tags.append(added_tag)
        if removed_tag != 0 and removed_tag in self.tags:
            self.tags.remove(removed_tag)

        if added_type:
            self.types.append(added_type)
        if removed_type and removed_type in self.types:
            self.types.remove(removed_type)
        if (self.types or self.price) or self.tags or self.ui.on_discount.isChecked():
            # self.free_scrollarea.setVisible(False)
            self.discounts_group.setVisible(False)
        else:
            # self.free_scrollarea.setVisible(True)
            if len(self.discounts_group.layout().children()) > 0:
                self.discounts_group.setVisible(True)

        self.games_group.loading(True)

        browse_model = SearchStoreQuery(
            language=self.core.language_code,
            country=self.core.country_code,
            count=20,
            price_range=self.price,
            on_sale=self.ui.on_discount.isChecked(),
        )
        browse_model.tag = "|".join(self.tags)

        if self.types:
            browse_model.category = "|".join(self.types)
        self.api_core.browse_games(browse_model, self.show_games)

    def show_games(self, data):
        for w in self.games_group.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            self.games_group.layout().removeWidget(w)
            w.deleteLater()

        if data:
            for game in data:
                w = GameWidget(self.api_core.cached_manager, game)
                w.show_info.connect(self.show_game)
                self.games_group.layout().addWidget(w)
        else:
            self.games_group.layout().addWidget(
                QLabel(self.tr("Could not get games matching the filter"))
            )
        self.games_group.loading(False)
        # FIXME: FlowLayout doesn't update on adding widget
        self.games_group.layout().update()


class CheckBox(QCheckBox):
    activated = pyqtSignal(str)
    deactivated = pyqtSignal(str)

    def __init__(self, text, tag):
        super(CheckBox, self).__init__(text)
        self.tag = tag

        self.toggled.connect(self.handle_toggle)

    def handle_toggle(self):
        if self.isChecked():
            self.activated.emit(self.tag)
        else:
            self.deactivated.emit(self.tag)
