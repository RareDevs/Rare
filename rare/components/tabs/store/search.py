import logging
from typing import List

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot
from PyQt5.QtWidgets import (
    QCheckBox,
    QWidget,
    QSizePolicy,
    QScrollArea,
    QFrame,
)
from legendary.core import LegendaryCore

from rare.ui.components.tabs.store.search import Ui_SearchWidget
from rare.utils.extra_widgets import ButtonLineEdit
from rare.widgets.side_tab import SideTabContents
from rare.widgets.sliding_stack import SlidingStackedWidget
from .api.models.query import SearchStoreQuery
from .api.models.response import CatalogOfferModel
from .constants import Constants
from .results import ResultsWidget
from .store_api import StoreAPI
from .widgets.details import DetailsWidget

logger = logging.getLogger("Shop")


class SearchPage(SlidingStackedWidget, SideTabContents):
    def __init__(self, core, api: StoreAPI, parent=None):
        super(SearchPage, self).__init__(parent=parent)
        self.implements_scrollarea = True

        self.search_widget = SearchWidget(core, api, parent=self)
        self.search_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_widget.set_title.connect(self.set_title)
        self.search_widget.show_details.connect(self.show_details)

        self.details_widget = DetailsWidget([], api, parent=self)
        self.details_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.details_widget.set_title.connect(self.set_title)
        self.details_widget.back_clicked.connect(self.show_main)

        self.details_scroll = QScrollArea(self)
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFrameStyle(QFrame.NoFrame | QFrame.Plain)
        self.details_scroll.setWidget(self.details_widget)

        self.setDirection(Qt.Horizontal)
        self.addWidget(self.search_widget)
        self.addWidget(self.details_scroll)

    @pyqtSlot()
    def show_main(self):
        self.slideInWidget(self.search_widget)

    @pyqtSlot(object)
    def show_details(self, game: CatalogOfferModel):
        self.details_widget.update_game(game)
        self.slideInWidget(self.details_scroll)


# noinspection PyAttributeOutsideInit,PyBroadException
class SearchWidget(QWidget, SideTabContents):
    show_details = pyqtSignal(CatalogOfferModel)

    def __init__(self, core: LegendaryCore, api: StoreAPI, parent=None):
        super(SearchWidget, self).__init__(parent=parent)
        self.implements_scrollarea = True
        self.ui = Ui_SearchWidget()
        self.ui.setupUi(self)
        self.ui.main_layout.setContentsMargins(0, 0, 3, 0)

        self.core = core
        self.api_core = api
        self.price = ""
        self.tags = []
        self.types = []
        self.update_games_allowed = True

        self.free_game_widgets = []
        self.active_search_request = False
        self.next_search = ""
        self.wishlist: List = []

        self.search_bar = ButtonLineEdit("fa.search", placeholder_text=self.tr("Search Games"))
        self.results_scrollarea = ResultsWidget(self.api_core, self)
        self.results_scrollarea.show_details.connect(self.show_details)

        self.ui.left_layout.addWidget(self.search_bar)
        self.ui.left_layout.addWidget(self.results_scrollarea)

        self.search_bar.returnPressed.connect(self.show_search_results)
        self.search_bar.buttonClicked.connect(self.show_search_results)

        # self.init_filter()

    def load(self):
        # load browse games
        self.prepare_request()

    def show_search_results(self):
        if text := self.search_bar.text():
            self.results_scrollarea.load_results(text)
            # self.show_info.emit(self.search_bar.text())

    def init_filter(self):
        self.ui.none_price.toggled.connect(
            lambda: self.prepare_request("") if self.ui.none_price.isChecked() else None
        )
        self.ui.free_button.toggled.connect(
            lambda: self.prepare_request("free") if self.ui.free_button.isChecked() else None
        )
        self.ui.under10.toggled.connect(
            lambda: self.prepare_request("<price>[0, 1000)") if self.ui.under10.isChecked() else None
        )
        self.ui.under20.toggled.connect(
            lambda: self.prepare_request("<price>[0, 2000)") if self.ui.under20.isChecked() else None
        )
        self.ui.under30.toggled.connect(
            lambda: self.prepare_request("<price>[0, 3000)") if self.ui.under30.isChecked() else None
        )
        self.ui.above.toggled.connect(
            lambda: self.prepare_request("<price>[1499,]") if self.ui.above.isChecked() else None
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
                checkbox.deactivated.connect(lambda x: self.prepare_request(removed_tag=x))
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
        self.update_games_allowed = False
        for cb in self.checkboxes:
            cb.setChecked(False)
        self.ui.none_price.setChecked(True)

        self.tags = []
        self.types = []
        self.update_games_allowed = True

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
