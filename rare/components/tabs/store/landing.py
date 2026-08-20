from datetime import datetime, timezone
from logging import getLogger

from PySide6.QtCore import QSize, Qt, Signal, Slot
from PySide6.QtGui import QHideEvent, QShowEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from rare.components.tabs.store.api.models.query import SearchStoreQuery
from rare.components.tabs.store.api.models.response import (
    CatalogOfferModel,
    WishlistItemModel,
)
from rare.shared import RareCore
from rare.widgets.button_edit import ButtonLineEdit
from rare.widgets.loading_widget import LoadingWidget
from rare.widgets.side_tab import SideTabContents
from rare.widgets.sliding_stack import SlidingStackedWidget

from .search import ResultsWidget
from .store_api import StoreAPI
from .widgets.details import StoreDetailsWidget
from .widgets.filters import FiltersWidget
from .widgets.groups import StoreGroup
from .widgets.items import StoreItemWidget

logger = getLogger('StoreLanding')


class LandingPage(SlidingStackedWidget, SideTabContents):
    open_library = Signal()

    def __init__(self, store_api: StoreAPI, rcore: RareCore | None = None, parent=None):
        super(LandingPage, self).__init__(parent=parent)
        self.implements_scrollarea = True
        self.api = store_api
        self.rcore = rcore

        self.landing_widget = LandingWidget(store_api, rcore, parent=self)
        self.landing_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.landing_widget.set_title.connect(self.set_title)
        self.landing_widget.show_details.connect(self.show_details)
        self.landing_widget.search_requested.connect(self.on_search)
        self._scrollbar = self.landing_widget.main_scroll.verticalScrollBar()
        self._scrollbar.valueChanged.connect(self._on_scroll)

        self.details_widget = StoreDetailsWidget(rcore, store_api, parent=self)
        self.details_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.details_widget.set_title.connect(self.set_title)
        self.details_widget.back_clicked.connect(self.show_main)
        self.details_widget.open_library.connect(self.open_library)

        self.setDirection(Qt.Orientation.Horizontal)
        self.addWidget(self.landing_widget)
        self.addWidget(self.details_widget)

        self.search_results = ResultsWidget(self.api, self.rcore, self)
        self.search_results.show_details.connect(self.show_details)
        self.search_back_btn = QPushButton(self.tr('Back to store'))
        self.search_back_btn.clicked.connect(self.show_main)
        self.search_container = QWidget(self)
        search_layout = QVBoxLayout(self.search_container)
        search_layout.setContentsMargins(0, 0, 3, 0)
        search_layout.addWidget(self.search_back_btn)
        search_layout.addWidget(self.search_results)
        self.addWidget(self.search_container)

    @Slot()
    def show_main(self):
        self.slideInWidget(self.landing_widget)

    @Slot(object)
    def show_details(self, game: CatalogOfferModel):
        self.details_widget.update_game(game)
        self.slideInWidget(self.details_widget)

    @Slot(str)
    def on_search(self, text: str):
        if text:
            self.api.search_game(text, self._on_search_results)

    def _on_search_results(self, results):
        self.search_results.show_results(results)
        self.slideInWidget(self.search_container)

    @Slot(int)
    def _on_scroll(self, value: int):
        if self._scrollbar.maximum() > 0 and value >= self._scrollbar.maximum() - 40:
            self.landing_widget.load_more_browse()


class LandingWidget(QWidget, SideTabContents):
    show_details = Signal(CatalogOfferModel)
    search_requested = Signal(str)

    def __init__(self, api: StoreAPI, rcore: RareCore | None = None, parent=None):
        super(LandingWidget, self).__init__(parent=parent)
        self.api = api
        self.rcore = rcore

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 3, 0)
        layout.setSpacing(12)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.main_column = QWidget(self)
        self.main_column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        main_layout = QVBoxLayout(self.main_column)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        self.search_bar = ButtonLineEdit('fa5s.search', placeholder_text=self.tr('Search'))
        self.search_bar.returnPressed.connect(lambda: self.search_requested.emit(self.search_bar.text()))
        self.search_bar.buttonClicked.connect(lambda: self.search_requested.emit(self.search_bar.text()))
        main_layout.addWidget(self.search_bar, alignment=Qt.AlignmentFlag.AlignTop)

        self.free_games_now = StoreGroup(self.tr('Free now'), parent=self.main_column)
        self.free_games_now.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.free_games_now.loading(True)

        self.free_games_next = StoreGroup(self.tr('Free next week'), parent=self.main_column)
        self.free_games_next.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.free_games_next.loading(True)

        self.discounts_group = StoreGroup(self.tr('Wishlist discounts'), parent=self.main_column)
        self.discounts_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.discounts_group.loading(True)

        self._browse_sections = {}
        self.free_to_play_group = self._create_browse_section('free', self.tr('Free to play'))
        self._browse_sections['free']['query'].price_range = 'free'
        self.on_sale_group = self._create_browse_section('sale', self.tr('On sale'))
        self._browse_sections['sale']['query'].on_sale = True
        self.discover_group = self._create_browse_section('discover', self.tr('Discover'))
        self.discover_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        main_layout.addWidget(self.free_games_now, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(self.free_games_next, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(self.free_to_play_group, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(self.discounts_group, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(self.on_sale_group, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(self.discover_group, stretch=1)

        self.main_scroll = QScrollArea(self)
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.main_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_scroll.setWidget(self.main_column)
        layout.addWidget(self.main_scroll, stretch=1)

        self.filters = FiltersWidget(self)
        self.filters.changed.connect(self._apply_filters)

        self.filters_column = QWidget(self)
        self.filters_column.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.filters_column.setMinimumWidth(240)
        self.filters_column.setMaximumWidth(280)
        filters_layout = QVBoxLayout(self.filters_column)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(6)

        self.reset_filters_btn = QPushButton(self.tr('Reset filters'))
        self.reset_filters_btn.clicked.connect(self.filters.reset)
        filters_layout.addWidget(self.reset_filters_btn)

        self.filters_scroll = QScrollArea(self)
        self.filters_scroll.setWidgetResizable(True)
        self.filters_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.filters_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.filters_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.filters_scroll.setWidget(self.filters)
        filters_layout.addWidget(self.filters_scroll)

        layout.addWidget(self.filters_column, stretch=0)

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)
        self.api.get_free(self._update_free_games)
        self.api.get_wishlist(self._update_wishlist_discounts)
        self._apply_filters()
        return super().showEvent(a0)

    def hideEvent(self, a0: QHideEvent) -> None:
        if a0.spontaneous():
            return super().hideEvent(a0)
        # TODO: Implement tab unloading
        return super().hideEvent(a0)

    def _update_wishlist_discounts(self, wishlist: list[WishlistItemModel]):
        self.discounts_group.clear_widgets()
        if not wishlist:
            self.discounts_group.setVisible(False)
            self.discounts_group.loading(False)
            return

        for item in filter(lambda x: bool(x.offer.price.totalPrice.discount), wishlist):
            w = StoreItemWidget(self.api.image_manager, item.offer, self.rcore)
            w.show_details.connect(self.show_details)
            self.discounts_group.add_widget(w)
        have_discounts = any(bool(x.offer.price.totalPrice.discount) for x in wishlist)
        self.discounts_group.setVisible(have_discounts)
        self.discounts_group.loading(False)

    def _update_free_games(self, free_games: list[CatalogOfferModel]):
        self.free_games_now.clear_widgets()
        self.free_games_next.clear_widgets()
        if not free_games:
            self.free_games_now.setVisible(False)
            self.free_games_next.setVisible(False)
            self.free_games_now.loading(False)
            self.free_games_next.loading(False)
            return

        date = datetime.now(timezone.utc)
        free_now = []
        free_next = []
        for item in free_games:
            try:
                if item.price.totalPrice.discountPrice == 0:
                    free_now.append(item)
                    continue
                if item.title == 'Mystery Game':
                    free_next.append(item)
                    continue
            except KeyError as e:
                logger.warning(str(e))

            if item.promotions is not None:
                if not item.promotions.upcomingPromotionalOffers and not item.promotions.promotionalOffers:
                    continue
                if not item.promotions.promotionalOffers:
                    start_date = item.promotions.upcomingPromotionalOffers[0].promotionalOffers[0].startDate
                else:
                    start_date = item.promotions.promotionalOffers[0].promotionalOffers[0].startDate

                if start_date > date:
                    free_next.append(item)

        # free games now
        self.free_games_now.setVisible(bool(free_now))
        for item in free_now:
            w = StoreItemWidget(self.api.image_manager, item, self.rcore)
            w.show_details.connect(self.show_details)
            self.free_games_now.add_widget(w)
        self.free_games_now.loading(False)

        # free games next week
        self.free_games_next.setVisible(bool(free_next))
        for item in free_next:
            w = StoreItemWidget(self.api.image_manager, item, self.rcore)
            if item.title != 'Mystery Game':
                w.show_details.connect(self.show_details)
            self.free_games_next.add_widget(w)
        self.free_games_next.loading(False)

    def _create_browse_section(self, name, title):
        group = StoreGroup(title, parent=self.main_column)
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        group.loading(True)
        spinner = LoadingWidget(parent=group)
        spinner.setFixedSize(QSize(48, 48))
        spinner.setVisible(False)
        self._browse_sections[name] = {
            'group': group,
            'query': SearchStoreQuery(),
            'start': 0,
            'loading': False,
            'has_more': True,
            'spinner': spinner,
            'hide_if_empty': name != 'discover',
        }
        return group

    def _reset_browse_section(self, name):
        state = self._browse_sections[name]
        state['start'] = 0
        state['has_more'] = True
        state['loading'] = False
        state['group'].clear_widgets()
        state['spinner'].setVisible(False)
        state['group'].loading(True)
        self._fetch_browse_section(name)

    def _fetch_browse_section(self, name):
        state = self._browse_sections[name]
        if state['loading'] or not state['has_more']:
            return
        state['loading'] = True
        if state['start'] > 0:
            state['spinner'].setVisible(True)
        state['query'].start = state['start']
        self.api.browse_games(state['query'], lambda elements: self._on_browse_section(name, elements))

    def _on_browse_section(self, name, elements):
        state = self._browse_sections[name]
        state['loading'] = False
        state['spinner'].setVisible(False)
        state['group'].loading(False)

        if state['start'] == 0 and not elements:
            if state['hide_if_empty']:
                state['group'].setVisible(False)
            else:
                state['group'].set_empty(self.tr('No games found'))
            return

        state['group'].setVisible(True)
        for game in elements:
            w = StoreItemWidget(self.api.image_manager, game, self.rcore)
            w.show_details.connect(self.show_details)
            state['group'].add_widget(w)

        state['start'] += len(elements)
        if len(elements) < state['query'].count:
            state['has_more'] = False

    def load_more_browse(self):
        self._fetch_browse_section('discover')

    def _apply_filters(self):
        query = SearchStoreQuery()
        self.filters.configure(query)
        self._browse_sections['discover']['query'] = query

        active = self.filters.is_active()
        self.free_games_now.setVisible(not active)
        self.free_games_next.setVisible(not active)
        self.discounts_group.setVisible(not active)
        self._browse_sections['free']['group'].setVisible(not active)
        self._browse_sections['sale']['group'].setVisible(not active)

        self._reset_browse_section('discover')
        if not active:
            self._reset_browse_section('free')
            self._reset_browse_section('sale')
