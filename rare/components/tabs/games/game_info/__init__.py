from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QWidget, QTabWidget
from qtawesome import icon

from rare.components.tabs.games.game_info.game_dlc import GameDlc
from rare.components.tabs.games.game_info.game_info import GameInfo
from rare.components.tabs.games.game_info.game_settings import GameSettings
from rare.utils.extra_widgets import SideTabBar


class InfoTabs(QTabWidget):
    def __init__(self, core, parent):
        super(InfoTabs, self).__init__(parent=parent)
        self.app_name = ""
        self.core = core
        self.setTabBar(SideTabBar())
        self.setTabPosition(QTabWidget.West)

        self.addTab(QWidget(), icon("mdi.keyboard-backspace"), self.tr("Back"))
        self.tabBarClicked.connect(lambda x: self.parent().layout.setCurrentIndex(0) if x == 0 else None)

        self.info = GameInfo(core, self)
        self.addTab(self.info, self.tr("Information"))

        self.settings = GameSettings(core, self)
        self.addTab(self.settings, self.tr("Settings"))
        self.tabBar().setCurrentIndex(1)

        self.dlc = GameDlc(core, self)
        self.addTab(self.dlc, self.tr("Downloadable Content"))

    def update_game(self, app_name, dlcs: list):

        self.info.update_game(app_name)
        self.settings.update_game(app_name)

        # DLC Tab: Disable if no dlcs available
        if dlcs:
            if len(dlcs[self.core.get_game(app_name).asset_info.catalog_item_id]) == 0:
                self.setTabEnabled(3, False)
            else:
                self.setTabEnabled(3, True)
                self.dlc.update_dlcs(app_name, dlcs)
        else:
            self.setTabEnabled(3, False)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Escape:
            self.parent().layout.setCurrentIndex(0)
