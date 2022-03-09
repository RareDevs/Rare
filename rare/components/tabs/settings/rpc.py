from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QGroupBox

from rare.shared import GlobalSignalsSingleton
from rare.ui.components.tabs.settings.rpc import Ui_RPCSettings


class RPCSettings(QGroupBox, Ui_RPCSettings):
    def __init__(self, parent):
        super(RPCSettings, self).__init__(parent=parent)
        self.setupUi(self)
        self.signals = GlobalSignalsSingleton()

        self.settings = QSettings()

        self.enable.setCurrentIndex(self.settings.value("rpc_enable", 0, int))
        self.enable.currentIndexChanged.connect(self.changed)

        self.show_game.setChecked((self.settings.value("rpc_name", True, bool)))
        self.show_game.stateChanged.connect(
            lambda: self.settings.setValue("rpc_game", self.show_game.isChecked())
        )

        self.show_os.setChecked((self.settings.value("rpc_os", True, bool)))
        self.show_os.stateChanged.connect(
            lambda: self.settings.setValue("rpc_os", self.show_os.isChecked())
        )

        self.show_time.setChecked((self.settings.value("rpc_time", True, bool)))
        self.show_time.stateChanged.connect(
            lambda: self.settings.setValue("rpc_time", self.show_time.isChecked())
        )

    def changed(self, i):
        self.settings.setValue("rpc_enable", i)
        self.signals.rpc_settings_updated.emit()
