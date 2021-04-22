from PyQt5.QtCore import QSettings, pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QCheckBox, QVBoxLayout, QComboBox


class RPCSettings(QGroupBox):
    update_settings = pyqtSignal()

    def __init__(self):
        super(RPCSettings, self).__init__()
        self.setTitle(self.tr("Discord RPC"))
        self.setObjectName("settings_widget")
        self.settings = QSettings()
        self.layout = QVBoxLayout()

        self.enable = QComboBox()
        self.enable_states = [self.tr("Show when playing"), self.tr("Show always"), self.tr("Show never")]
        self.enable.addItems(self.enable_states)
        self.enable.setCurrentIndex(self.settings.value("rpc_enable", 0, int))
        self.layout.addWidget(self.enable)
        self.enable.currentIndexChanged.connect(self.changed)

        self.show_game = QCheckBox(self.tr("Show Game"))
        self.show_game.setChecked((self.settings.value("rpc_name", True, bool)))
        self.layout.addWidget(self.show_game)
        self.show_game.stateChanged.connect(lambda: self.settings.setValue("rpc_game", self.show_game.isChecked()))

        self.show_os = QCheckBox(self.tr("Show OS"))
        self.layout.addWidget(self.show_os)
        self.show_os.setChecked((self.settings.value("rpc_os", True, bool)))
        self.show_os.stateChanged.connect(lambda: self.settings.setValue("rpc_os", self.show_os.isChecked()))

        self.show_time = QCheckBox(self.tr("Show Time playing"))
        self.layout.addWidget(self.show_time)
        self.show_time.setChecked((self.settings.value("rpc_time", True, bool)))
        self.show_time.stateChanged.connect(lambda: self.settings.setValue("rpc_time", self.show_time.isChecked()))

        self.setLayout(self.layout)

    def changed(self, i):
        self.settings.setValue("rpc_enable", i)
        self.update_settings.emit()
