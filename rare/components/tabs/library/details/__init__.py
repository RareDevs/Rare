from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QTreeView

from rare.models.game import RareGame
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton, ArgumentsSingleton
from rare.utils.json_formatter import QJsonModel
from rare.widgets.side_tab import SideTabWidget, SideTabContents
from .dlcs import GameDlcs
from .details import GameDetails
from .settings import GameSettings
from .cloud_saves import CloudSaves


class GameInfoTabs(SideTabWidget):
    # str: app_name
    import_clicked = Signal(str)

    def __init__(self, parent=None):
        super(GameInfoTabs, self).__init__(show_back=True, parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()

        self.details_tab = GameDetails(self)
        self.details_tab.import_clicked.connect(self.import_clicked)
        self.details_index = self.addTab(self.details_tab, self.tr("Information"))

        self.settings_tab = GameSettings(self)
        self.settings_index = self.addTab(self.settings_tab, self.tr("Settings"))

        self.cloud_saves_tab = CloudSaves(self)
        self.cloud_saves_index = self.addTab(self.cloud_saves_tab, self.tr("Cloud Saves"))

        self.dlcs_tab = GameDlcs(self)
        self.dlcs_index = self.addTab(self.dlcs_tab, self.tr("Downloadable Content"))

        # FIXME: Hiding didn't work, so don't add these tabs in normal mode. Fix this properly later
        if self.args.debug:
            self.game_meta_view = GameMetadataView(self)
            self.game_meta_index = self.addTab(self.game_meta_view, self.tr("Game Metadata"))
            self.igame_meta_view = GameMetadataView(self)
            self.igame_meta_index = self.addTab(self.igame_meta_view, self.tr("InstalledGame Metadata"))
            self.rgame_meta_view = GameMetadataView(self)
            self.rgame_meta_index = self.addTab(self.rgame_meta_view, self.tr("RareGame Metadata"))

        self.setCurrentIndex(self.details_index)

    def update_game(self, rgame: RareGame):
        self.details_tab.update_game(rgame)

        self.settings_tab.load_settings(rgame)
        self.settings_tab.setEnabled(rgame.is_installed or rgame.is_origin)

        self.dlcs_tab.update_dlcs(rgame)
        self.dlcs_tab.setEnabled(rgame.is_installed and bool(rgame.owned_dlcs))

        self.cloud_saves_tab.update_game(rgame)
        # self.cloud_saves_tab.setEnabled(rgame.game.supports_cloud_saves or rgame.game.supports_mac_cloud_saves)

        if self.args.debug:
            self.game_meta_view.update_game(rgame, rgame.game)
            self.igame_meta_view.update_game(rgame, rgame.igame)
            self.rgame_meta_view.update_game(rgame, rgame.metadata)

        self.setCurrentIndex(self.details_index)

    def keyPressEvent(self, a0: QKeyEvent):
        if a0.key() == Qt.Key.Key_Escape:
            self.back_clicked.emit()


class GameMetadataView(QTreeView, SideTabContents):
    def __init__(self, parent=None):
        super(GameMetadataView, self).__init__(parent=parent)
        self.implements_scrollarea = True
        self.setColumnWidth(0, 300)
        self.setWordWrap(True)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.model = QJsonModel()
        self.setModel(self.model)
        self.rgame: Optional[RareGame] = None

    def update_game(self, rgame: RareGame, view):
        self.rgame = rgame
        self.set_title.emit(self.rgame.app_title)
        self.model.clear()
        try:
            self.model.load(vars(view))
        except Exception as e:
            pass
        self.resizeColumnToContents(0)
