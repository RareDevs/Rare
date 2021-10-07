from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QWidget, QTabWidget
from qtawesome import icon

from legendary.models.game import Game
from rare.components.tabs.games.game_info.game_dlc import GameDlc
from rare.components.tabs.games.game_info.game_info import GameInfo
from rare.components.tabs.games.game_info.game_settings import GameSettings
from rare.utils.extra_widgets import SideTabBar
from rare.utils.models import Signals


class InfoTabs(QTabWidget):
    def __init__(self, core, signals: Signals, parent):
        super(InfoTabs, self).__init__(parent=parent)
        self.app_name = ""
        self.core = core
        self.signals = signals
        self.setTabBar(SideTabBar())
        self.setTabPosition(QTabWidget.West)

        self.addTab(QWidget(), icon("mdi.keyboard-backspace"), self.tr("Back"))
        self.tabBarClicked.connect(lambda x: self.parent().setCurrentIndex(0) if x == 0 else None)

        self.info = GameInfo(self.core, self.signals, self)
        self.addTab(self.info, self.tr("Information"))

        self.settings = GameSettings(core, self)
        self.addTab(self.settings, self.tr("Settings"))
        self.tabBar().setCurrentIndex(1)

        self.dlc = GameDlc(core, self.signals, self)
        self.addTab(self.dlc, self.tr("Downloadable Content"))

    def update_game(self, game: Game, dlcs: list):
        self.setCurrentIndex(1)
        self.info.update_game(game)
        self.settings.update_game(game)

        # DLC Tab: Disable if no dlcs available
        if dlcs:
            if len(dlcs[game.asset_info.catalog_item_id]) == 0:
                self.setTabEnabled(3, False)
            else:
                self.setTabEnabled(3, True)
                self.dlc.update_dlcs(game.app_name, dlcs)
        else:
            self.setTabEnabled(3, False)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Escape:
            self.parent().layout().setCurrentIndex(0)
