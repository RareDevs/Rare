import importlib.util

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox

from rare.shared import RareCore
from rare.models.settings import settings, RareAppSettings, DiscordRPCMode
from rare.ui.components.tabs.settings.widgets.discord_rpc import Ui_DiscordRPCSettings


class DiscordRPCSettings(QGroupBox):
    def __init__(self, parent):
        super(DiscordRPCSettings, self).__init__(parent=parent)
        self.ui = Ui_DiscordRPCSettings()
        self.ui.setupUi(self)
        self.signals = RareCore.instance().signals()

        self.ui.mode_combo.addItem(self.tr("When playing"), DiscordRPCMode.GAME_ONLY)
        self.ui.mode_combo.addItem(self.tr("Always"), DiscordRPCMode.ALWAYS)
        self.ui.mode_combo.addItem(self.tr("Never"), DiscordRPCMode.NEVER)

        self.settings = RareAppSettings.instance()

        rpc_mode = DiscordRPCMode(self.settings.get_value(settings.discord_rpc_mode))
        if (index := self.ui.mode_combo.findData(rpc_mode, Qt.ItemDataRole.UserRole)) < 0:
            self.settings.set_value(settings.discord_rpc_mode, settings.discord_rpc_mode.default)
            rpc_mode = DiscordRPCMode(settings.discord_rpc_mode.default)
            self.ui.mode_combo.setCurrentIndex(self.ui.mode_combo.findData(rpc_mode, Qt.ItemDataRole.UserRole))
        else:
            self.ui.mode_combo.setCurrentIndex(index)
        self.ui.mode_combo.currentIndexChanged.connect(self.__mode_changed)

        self.ui.game_check.setChecked(self.settings.get_value(settings.discord_rpc_game))
        self.ui.game_check.checkStateChanged.connect(
            lambda s: self.settings.set_value(settings.discord_rpc_game, s != Qt.CheckState.Unchecked)
        )

        self.ui.os_check.setChecked(self.settings.get_value(settings.discord_rpc_os))
        self.ui.os_check.checkStateChanged.connect(
            lambda s: self.settings.set_value(settings.discord_rpc_os, s != Qt.CheckState.Unchecked)
        )

        self.ui.time_check.setChecked(self.settings.get_value(settings.discord_rpc_time))
        self.ui.time_check.checkStateChanged.connect(
            lambda s: self.settings.set_value(settings.discord_rpc_time, s != Qt.CheckState.Unchecked)
        )

        if not importlib.util.find_spec("pypresence"):
            self.setDisabled(True)
            self.setToolTip(self.tr("Pypresence is not installed"))

    def __mode_changed(self, index):
        data = self.ui.mode_combo.itemData(index, Qt.ItemDataRole.UserRole)
        self.settings.set_value(settings.discord_rpc_mode, data)
        self.signals.discord_rpc.update_settings.emit()
