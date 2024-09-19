from logging import getLogger

from PySide6.QtCore import QSettings, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget, QScrollArea, QFrame

from rare.models.game import RareGame
from rare.shared import (
    LegendaryCoreSingleton,
    GlobalSignalsSingleton,
    ArgumentsSingleton,
    ImageManagerSingleton,
)
from rare.shared import RareCore
from rare.models.options import options
from .details import GameInfoTabs
from .widgets import LibraryWidgetController, LibraryFilter, LibraryOrder, LibraryView
from .head_bar import LibraryHeadBar
from .integrations import IntegrationsTabs

logger = getLogger("GamesLibrary")


class GamesLibrary(QStackedWidget):
    def __init__(self, parent=None):
        super(GamesLibrary, self).__init__(parent=parent)
        self.rcore = RareCore.instance()
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()
        self.image_manager = ImageManagerSingleton()
        self.settings = QSettings()

        self.games_page = QWidget(parent=self)
        games_page_layout = QVBoxLayout(self.games_page)
        self.addWidget(self.games_page)

        self.head_bar = LibraryHeadBar(parent=self.games_page)
        self.head_bar.goto_import.connect(self.show_import)
        self.head_bar.goto_egl_sync.connect(self.show_egl_sync)
        self.head_bar.goto_eos_ubisoft.connect(self.show_eos_ubisoft)
        games_page_layout.addWidget(self.head_bar)

        self.game_info_page = GameInfoTabs(self)
        self.game_info_page.back_clicked.connect(lambda: self.setCurrentWidget(self.games_page))
        self.game_info_page.import_clicked.connect(self.show_import)
        self.addWidget(self.game_info_page)

        self.integrations_page = IntegrationsTabs(self)
        self.integrations_page.back_clicked.connect(lambda: self.setCurrentWidget(self.games_page))
        self.addWidget(self.integrations_page)

        self.view_scroll = QScrollArea(self.games_page)
        self.view_scroll.setWidgetResizable(True)
        self.view_scroll.setFrameShape(QFrame.Shape.StyledPanel)
        self.view_scroll.horizontalScrollBar().setDisabled(True)

        library_view = LibraryView(self.settings.value(*options.library_view))
        self.library_controller = LibraryWidgetController(library_view, self.view_scroll)
        games_page_layout.addWidget(self.view_scroll)

        self.head_bar.search_bar.textChanged.connect(self.search_games)
        self.head_bar.search_bar.textChanged.connect(self.scroll_to_top)
        self.head_bar.filterChanged.connect(self.filter_games)
        self.head_bar.filterChanged.connect(self.scroll_to_top)
        self.head_bar.orderChanged.connect(self.order_games)
        self.head_bar.orderChanged.connect(self.scroll_to_top)
        self.head_bar.refresh_list.clicked.connect(self.library_controller.update_game_views)

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
        self.view_scroll.verticalScrollBar().setSliderPosition(
            self.view_scroll.verticalScrollBar().minimum()
        )

    @Slot()
    @Slot(str)
    def show_import(self, app_name: str = None):
        self.setCurrentWidget(self.integrations_page)
        self.integrations_page.show_import(app_name)

    @Slot()
    def show_egl_sync(self):
        self.setCurrentWidget(self.integrations_page)
        self.integrations_page.show_egl_sync()

    @Slot()
    def show_eos_ubisoft(self):
        self.setCurrentWidget(self.integrations_page)
        self.integrations_page.show_eos_ubisoft()

    @Slot(RareGame)
    def show_game_info(self, rgame):
        self.game_info_page.update_game(rgame)
        self.setCurrentWidget(self.game_info_page)

    @Slot()
    def update_count_games_label(self):
        self.head_bar.set_games_count(
            len([game for game in self.rcore.games if game.is_installed]),
            len(list(self.rcore.games)),
        )

    def setup_game_list(self):
        for rgame in self.rcore.games:
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
    def filter_games(self, library_filter: LibraryFilter = LibraryFilter.ALL, search_text: str = ""):
        if not search_text and (t := self.head_bar.search_bar.text()):
            search_text = t

        self.library_controller.filter_game_views(library_filter, search_text.lower())

    @Slot(object)
    @Slot(object, str)
    def order_games(self, library_order: LibraryOrder = LibraryFilter.ALL, search_text: str = ""):
        if not search_text and (t := self.head_bar.search_bar.text()):
            search_text = t

        self.library_controller.order_game_views(library_order, search_text.lower())
