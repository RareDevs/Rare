from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QTreeView
from legendary.models.game import Game

from rare.components.tabs.games.game_utils import GameUtils
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.utils.extra_widgets import SideTabWidget
from rare.utils.json_formatter import QJsonModel
from .game_dlc import GameDlc
from .game_info import GameInfo
from .game_settings import GameSettings


class GameInfoTabs(SideTabWidget):
    def __init__(self, dlcs: dict, game_utils: GameUtils, parent=None):
        super(GameInfoTabs, self).__init__(show_back=True, parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        self.info = GameInfo(self, game_utils)
        self.addTab(self.info, self.tr("Information"))

        self.settings = GameSettings(self)
        self.addTab(self.settings, self.tr("Settings"))

        self.dlc_list = dlcs
        self.dlc = GameDlc(self.dlc_list, game_utils, self)
        self.addTab(self.dlc, self.tr("Downloadable Content"))

        self.view = GameMetadataView()
        self.addTab(self.view, self.tr("Metadata"))

        self.tabBar().setCurrentIndex(1)

    def update_game(self, app_name: str):
        installed = bool(self.core.get_installed_game(app_name))

        self.info.update_game(app_name)

        self.settings.load_settings(app_name)
        self.settings.setEnabled(installed)

        self.dlc.setEnabled(
            not bool(len(self.dlc_list.get(self.core.get_game(app_name).catalog_item_id, [])) == 0)
        )
        self.dlc.update_dlcs(app_name)

        self.view.update_game(self.core.get_game(app_name))

        self.setCurrentIndex(1)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Escape:
            self.parent().layout().setCurrentIndex(0)


class GameMetadataView(QTreeView):
    def __init__(self, parent=None):
        super(GameMetadataView, self).__init__(parent=parent)
        self.setColumnWidth(0, 300)
        self.setWordWrap(True)
        self.model = QJsonModel()
        self.setModel(self.model)
        self.game: Optional[Game] = None

    def update_game(self, game: Game):
        self.game = game
        self.title.setTitle(self.game.app_title)
        self.model.clear()
        try:
            self.model.load(game.__dict__)
        except:
            pass
        self.resizeColumnToContents(0)
