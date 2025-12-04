from logging import getLogger

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QShowEvent  # , Qt, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    # QLineEdit,
    # QListWidget,
    # QListWidgetItem,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# from rare.models.image import ImageSize
from rare.models.game import RareGame
from rare.models.settings import RareAppSettings, app_settings
from rare.shared import RareCore

from .details import GameDetailsTabs
from .head_bar import LibraryHeadBar
from .widgets import LibraryFilter, LibraryOrder, LibraryView, LibraryWidgetController

logger = getLogger("GamesLibrary")


class GamesLibrary(QStackedWidget):
    exit_app: Signal = Signal(int)
    # str: app_name
    import_clicked = Signal(str)

    def __init__(self, settings: RareAppSettings, rcore: RareCore, parent=None):
        super(GamesLibrary, self).__init__(parent=parent)
        self.settings = settings
        self.rcore = rcore
        self.signals = rcore.signals()

        self.library_page = QWidget(parent=self)
        library_page_layout = QHBoxLayout(self.library_page)
        # library_page_left_layout = QVBoxLayout()
        # library_page_layout.addLayout(library_page_left_layout, stretch=0)
        library_page_right_layout = QVBoxLayout()
        library_page_layout.addLayout(library_page_right_layout, stretch=2)
        self.addWidget(self.library_page)

        # self.library_search = QLineEdit(self.library_page)
        # library_page_left_layout.addWidget(self.library_search)

        # self.library_list = QListWidget(self.library_page)
        # self.library_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.library_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # library_page_left_layout.addWidget(self.library_list)

        self.head_bar = LibraryHeadBar(settings, rcore, parent=self.library_page)
        self.head_bar.exit_app.connect(self.exit_app)
        library_page_right_layout.addWidget(self.head_bar)

        self.details_page = GameDetailsTabs(settings, rcore, self)
        self.details_page.back_clicked.connect(lambda: self.setCurrentWidget(self.library_page))
        # Update visibility of hidden games
        self.details_page.back_clicked.connect(lambda: self.filter_games(self.head_bar.current_filter()))
        self.details_page.import_clicked.connect(self.import_clicked)
        self.addWidget(self.details_page)

        self.view_scroll = QScrollArea(self.library_page)
        self.view_scroll.setWidgetResizable(True)
        self.view_scroll.setFrameShape(QFrame.Shape.StyledPanel)
        self.view_scroll.horizontalScrollBar().setDisabled(True)

        library_view = LibraryView(self.settings.get_value(app_settings.library_view))
        library_page_right_layout.addWidget(self.view_scroll)

        self.library_controller = LibraryWidgetController(rcore, library_view, self.view_scroll)

        self.head_bar.search_bar.textChanged.connect(self.search_games)
        self.head_bar.search_bar.textChanged.connect(self.scroll_to_top)
        self.head_bar.filterChanged.connect(self.filter_games)
        self.head_bar.filterChanged.connect(self.scroll_to_top)
        self.head_bar.orderChanged.connect(self.order_games)
        self.head_bar.orderChanged.connect(self.scroll_to_top)

        # signals
        self.signals.game.installed.connect(self.update_count_games_label)
        self.signals.game.uninstalled.connect(self.update_count_games_label)

        self.init = True

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous() or not self.init:
            return super().showEvent(a0)
        self.setup_game_list()
        self.init = False
        return super().showEvent(a0)

    @Slot()
    def scroll_to_top(self):
        self.view_scroll.verticalScrollBar().setSliderPosition(self.view_scroll.verticalScrollBar().minimum())

    @Slot()
    def show_library(self):
        self.setCurrentWidget(self.library_page)

    @Slot(RareGame)
    def show_game_info(self, rgame):
        self.details_page.update_game(rgame)
        self.setCurrentWidget(self.details_page)

    @Slot()
    def update_count_games_label(self):
        self.head_bar.set_games_count(
            len([game for game in self.rcore.games if game.is_installed]),
            len(list(self.rcore.games)),
        )

    def setup_game_list(self):
        for rgame in self.rcore.games:
            # self.library_list.addItem(QListWidgetItem(QIcon(rgame.get_pixmap(ImageSize.Icon)), rgame.app_title))
            widget = self.add_library_widget(rgame)
            if not widget:
                logger.warning("Excluding %s from the game list", rgame.app_title)
                continue
        self.filter_games(self.head_bar.current_filter())
        self.order_games(self.head_bar.current_order())
        self.update_count_games_label()

    def add_library_widget(self, rgame: RareGame):
        try:
            widget = self.library_controller.add_game(rgame)
        except Exception as e:
            logger.error("Could not add widget for %s to library: %s", rgame.app_name, e)
            return None
        widget.show_info.connect(self.show_game_info)
        return widget

    @Slot(str)
    def search_games(self, search_text: str = ""):
        self.filter_games(self.head_bar.current_filter(), search_text)

    @Slot(object)
    @Slot(object, str)
    def filter_games(self, library_filter: LibraryFilter = None, search_text: str = ""):
        if not search_text and (t := self.head_bar.search_bar.text()):
            search_text = t

        self.library_controller.filter_game_view(library_filter, search_text.lower())

    @Slot(object)
    @Slot(object, str)
    def order_games(self, library_order: LibraryOrder = None, search_text: str = ""):
        if not search_text and (t := self.head_bar.search_bar.text()):
            search_text = t

        self.library_controller.order_game_view(library_order, search_text.lower())
