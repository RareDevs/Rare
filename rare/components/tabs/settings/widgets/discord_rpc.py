import importlib.util

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QGroupBox

from rare.models.settings import DiscordRPCMode, RareAppSettings, app_settings
from rare.models.signals import GlobalSignals
from rare.ui.components.tabs.settings.widgets.discord_rpc import Ui_DiscordRPCSettings


class DiscordRPCSettings(QGroupBox):
    def __init__(self, settings: RareAppSettings, signals: GlobalSignals, parent):
        super(DiscordRPCSettings, self).__init__(parent=parent)
        self.settings = settings
        self.signals = signals

        self.ui = Ui_DiscordRPCSettings()
        self.ui.setupUi(self)

        self.ui.mode_combo.addItem(self.tr("When playing"), DiscordRPCMode.GAME_ONLY)
        self.ui.mode_combo.addItem(self.tr("Always"), DiscordRPCMode.ALWAYS)
        self.ui.mode_combo.addItem(self.tr("Never"), DiscordRPCMode.NEVER)

        rpc_mode = DiscordRPCMode(self.settings.get_value(app_settings.discord_rpc_mode))
        if (index := self.ui.mode_combo.findData(rpc_mode, Qt.ItemDataRole.UserRole)) < 0:
            self.settings.set_value(app_settings.discord_rpc_mode, app_settings.discord_rpc_mode.default)
            rpc_mode = DiscordRPCMode(app_settings.discord_rpc_mode.default)
            self.ui.mode_combo.setCurrentIndex(self.ui.mode_combo.findData(rpc_mode, Qt.ItemDataRole.UserRole))
        else:
            self.ui.mode_combo.setCurrentIndex(index)
        self.ui.mode_combo.currentIndexChanged.connect(self._mode_changed)

        self.ui.game_check.setChecked(self.settings.get_value(app_settings.discord_rpc_game))
        self.ui.game_check.checkStateChanged.connect(self._on_game_changed)

        self.ui.os_check.setChecked(self.settings.get_value(app_settings.discord_rpc_os))
        self.ui.os_check.checkStateChanged.connect(self._on_os_changed)

        self.ui.time_check.setChecked(self.settings.get_value(app_settings.discord_rpc_time))
        self.ui.time_check.checkStateChanged.connect(self._on_time_changed)

        if not importlib.util.find_spec("pypresence"):
            self.setDisabled(True)
            self.setToolTip(self.tr("Pypresence is not installed"))

    @Slot(Qt.CheckState)
    def _on_game_changed(self, state: Qt.CheckState):
        self.settings.set_value(app_settings.discord_rpc_game, state != Qt.CheckState.Unchecked)

    @Slot(Qt.CheckState)
    def _on_os_changed(self, state: Qt.CheckState):
        self.settings.set_value(app_settings.discord_rpc_os, state != Qt.CheckState.Unchecked)

    @Slot(Qt.CheckState)
    def _on_time_changed(self, state: Qt.CheckState):
        self.settings.set_value(app_settings.discord_rpc_time, state != Qt.CheckState.Unchecked)

    @Slot(int)
    def _mode_changed(self, index: int):
        data = self.ui.mode_combo.itemData(index, Qt.ItemDataRole.UserRole)
        self.settings.set_value(app_settings.discord_rpc_mode, data)
        self.signals.discord_rpc.update_settings.emit()
