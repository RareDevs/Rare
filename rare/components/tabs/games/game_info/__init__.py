from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QTreeView

from rare.components.tabs.games.game_utils import GameUtils
from rare.models.game import RareGame
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.utils.extra_widgets import SideTabWidget
from rare.utils.json_formatter import QJsonModel
from .game_dlc import GameDlc
from .game_info import GameInfo
from .game_settings import GameSettings


class GameInfoTabs(SideTabWidget):
    def __init__(self, game_utils: GameUtils, parent=None):
        super(GameInfoTabs, self).__init__(show_back=True, parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        self.info = GameInfo(game_utils, self)
        self.addTab(self.info, self.tr("Information"))

        self.settings = GameSettings(self)
        self.addTab(self.settings, self.tr("Settings"))

        self.dlc = GameDlc(game_utils, self)
        self.addTab(self.dlc, self.tr("Downloadable Content"))

        self.view = GameMetadataView()
        self.addTab(self.view, self.tr("Metadata"))

        self.tabBar().setCurrentIndex(1)

    def update_game(self, rgame: RareGame):
        self.info.update_game(rgame)

        self.settings.load_settings(rgame)
        self.settings.setEnabled(rgame.is_installed)

        self.dlc.update_dlcs(rgame)
        self.dlc.setEnabled(bool(rgame.owned_dlcs))

        self.view.update_game(rgame)

        self.setCurrentIndex(1)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Escape:
            self.back_clicked.emit()


class GameMetadataView(QTreeView):
    def __init__(self, parent=None):
        super(GameMetadataView, self).__init__(parent=parent)
        self.setColumnWidth(0, 300)
        self.setWordWrap(True)
        self.model = QJsonModel()
        self.setModel(self.model)
        self.rgame: Optional[RareGame] = None

    def update_game(self, rgame: RareGame):
        self.rgame = rgame
        self.title.setTitle(self.rgame.app_title)
        self.model.clear()
        try:
            self.model.load(rgame.game.__dict__)
        except Exception as e:
            pass
        self.resizeColumnToContents(0)
