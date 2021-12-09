from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent

import rare.shared as shared
from rare.utils.extra_widgets import SideTabWidget
from .game_dlc import GameDlc
from .game_info import GameInfo
from .game_settings import GameSettings
from ..game_utils import GameUtils


class GameInfoTabs(SideTabWidget):
    def __init__(self, dlcs: dict, game_utils: GameUtils, parent=None):
        super(GameInfoTabs, self).__init__(show_back=True, parent=parent)
        self.core = shared.core
        self.signals = shared.signals

        self.info = GameInfo(self, game_utils)
        self.addTab(self.info, self.tr("Information"))

        self.settings = GameSettings(self.core, self)
        self.addTab(self.settings, self.tr("Settings"))

        self.dlc_list = dlcs
        self.dlc = GameDlc(self.dlc_list, game_utils, self)
        self.addTab(self.dlc, self.tr("Downloadable Content"))

        self.tabBar().setCurrentIndex(1)

    def update_game(self, app_name: str):
        self.setCurrentIndex(1)
        self.info.update_game(app_name)
        self.settings.update_game(app_name)

        # DLC Tab: Disable if no dlcs available
        if len(self.dlc_list.get(self.core.get_game(app_name).catalog_item_id, [])) == 0:
            self.setTabEnabled(3, False)
        else:
            self.setTabEnabled(3, True)
            self.dlc.update_dlcs(app_name)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Escape:
            self.parent().layout().setCurrentIndex(0)
