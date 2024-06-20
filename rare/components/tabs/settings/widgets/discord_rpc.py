from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QGroupBox

from rare.shared import GlobalSignalsSingleton
from rare.models.options import options
from rare.ui.components.tabs.settings.widgets.discord_rpc import Ui_DiscordRPCSettings


class DiscordRPCSettings(QGroupBox):
    def __init__(self, parent):
        super(DiscordRPCSettings, self).__init__(parent=parent)
        self.ui = Ui_DiscordRPCSettings()
        self.ui.setupUi(self)
        self.signals = GlobalSignalsSingleton()

        self.settings = QSettings()

        self.ui.enable.setCurrentIndex(self.settings.value(*options.discord_rpc_mode))
        self.ui.enable.currentIndexChanged.connect(self.__enable_changed)

        self.ui.show_game.setChecked((self.settings.value(*options.discord_rpc_game)))
        self.ui.show_game.stateChanged.connect(
            lambda: self.settings.setValue(options.discord_rpc_game.key, self.ui.show_game.isChecked())
        )

        self.ui.show_os.setChecked((self.settings.value(*options.discord_rpc_os)))
        self.ui.show_os.stateChanged.connect(
            lambda: self.settings.setValue(options.discord_rpc_os.key, self.ui.show_os.isChecked())
        )

        self.ui.show_time.setChecked((self.settings.value(*options.discord_rpc_time)))
        self.ui.show_time.stateChanged.connect(
            lambda: self.settings.setValue(options.discord_rpc_time.key, self.ui.show_time.isChecked())
        )

        try:
            import pypresence
        except ModuleNotFoundError:
            self.setDisabled(True)
            self.setToolTip(self.tr("Pypresence is not installed"))

    def __enable_changed(self, i):
        self.settings.setValue(options.discord_rpc_mode.key, i)
        self.signals.discord_rpc.update_settings.emit()
