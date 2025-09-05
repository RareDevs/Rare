import platform as pf
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QShowEvent
from PySide6.QtWidgets import QTreeView

from rare.models.game import RareGame
from rare.models.settings import RareAppSettings
from rare.shared import RareCore
from rare.utils.json_formatter import QJsonModel
from rare.widgets.side_tab import SideTabWidget, SideTabContents
from .cloud_saves import CloudSaves
from .compat import LocalCompatSettings
from .details import GameDetails
from .dlcs import GameDlcs
from .game import LocalGameSettings


class GameInfoTabs(SideTabWidget):
    # str: app_name
    import_clicked = Signal(str)

    def __init__(self, settings: RareAppSettings, rcore: RareCore, parent=None):
        super(GameInfoTabs, self).__init__(show_back=True, parent=parent)
        self.rcore = rcore
        self.core = rcore.core()
        self.signals = rcore.signals()
        self.args = rcore.args()

        self.details_tab = GameDetails(self.rcore, self)
        self.details_tab.import_clicked.connect(self.import_clicked)
        self.details_index = self.addTab(self.details_tab, self.tr("Information"))

        self.game_settings_tab = LocalGameSettings(settings, rcore, self)
        self.game_settings_index = self.addTab(self.game_settings_tab, self.tr("Settings"))

        if pf.system() != "Windows":
            self.compat_settings_tab = LocalCompatSettings(settings, rcore, self)
            self.compat_settings_index = self.addTab(self.compat_settings_tab, self.tr("Compatibility"))

        self.cloud_saves_tab = CloudSaves(settings, rcore, self)
        self.cloud_saves_index = self.addTab(self.cloud_saves_tab, self.tr("Cloud Saves"))

        self.dlcs_tab = GameDlcs(rcore, self)
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

        self.game_settings_tab.load_settings(rgame)
        self.game_settings_tab.launch.setEnabled(rgame.is_installed or rgame.is_origin)
        self.game_settings_tab.env_vars.setEnabled(rgame.is_installed or rgame.is_origin)

        if pf.system() != "Windows":
            self.compat_settings_tab.load_settings(rgame)
            self.compat_settings_tab.setEnabled(rgame.is_installed or rgame.is_origin)

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

    def showEvent(self, event: QShowEvent):
        if event.spontaneous():
            return super().showEvent(event)
        super().showEvent(event)

    def update_game(self, rgame: RareGame, view):
        self.rgame = rgame
        self.set_title.emit(self.rgame.app_title)
        self.model.clear()
        try:
            self.model.load(vars(view))
        except Exception:
            pass
        self.resizeColumnToContents(0)
