from logging import getLogger

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QLineEdit
from custom_legendary.core import LegendaryCore

from Rare.Components.Tabs.Settings.DXVK.Dxvk import DxvkWidget
from Rare.Components.Tabs.Settings.SettingsWidget import SettingsWidget
from Rare.utils.QtExtensions import PathEdit

logger = getLogger("LinuxSettings")


class LinuxSettings(QWidget):
    def __init__(self, core: LegendaryCore, name="default"):
        super(LinuxSettings, self).__init__()
        self.layout = QVBoxLayout()
        self.name = name
        self.core = core
        self.title = QLabel("<h2>Linux settings</h2>")
        self.layout.addWidget(self.title)

        # Wineprefix
        self.select_path = PathEdit(self.core.lgd.config.get(self.name, "wine_prefix", fallback=""),
                                    type_of_file=QFileDialog.DirectoryOnly,
                                    infotext="Default")
        self.select_path.text_edit.textChanged.connect(lambda t: self.save_path_button.setDisabled(False))
        self.save_path_button = QPushButton("Save")
        self.save_path_button.clicked.connect(self.save_wineprefix)
        self.install_dir_widget = SettingsWidget(self.tr("Default Wine Prefix"), self.select_path,
                                                 self.save_path_button)
        self.layout.addWidget(self.install_dir_widget)

        # Wine executable
        self.select_wine_exec = QLineEdit(self.core.lgd.config.get(self.name, "wine_executable", fallback=""))
        self.save_wine_exec = QPushButton("Save")
        self.save_wine_exec.clicked.connect(self.save_wineexec)
        self.install_dir_widget = SettingsWidget(self.tr("Default Wine executable"), self.select_wine_exec,
                                                 self.save_wine_exec)
        self.layout.addWidget(self.install_dir_widget)

        # dxvk
        self.dxvk_widget = DxvkWidget(core)
        self.layout.addWidget(self.dxvk_widget)
        if name == "default":
            self.layout.addStretch(1)
        self.setLayout(self.layout)

    def save_wineprefix(self):
        if not self.name in self.core.lgd.config.sections():
            self.core.lgd.config[self.name] = dict()
        self.core.lgd.config[self.name]["wine_prefix"] = self.select_path.text()
        if self.select_path.text() == "":
            self.core.lgd.config[self.name].pop("wine_prefix")
            logger.info("Remove wine_prefix section")
        else:
            logger.info("Set config of wine_prefix to " + self.select_path.text())
        if self.core.lgd.config[self.name] == {}:
            self.core.lgd.config.remove_section(self.name)
        self.core.lgd.save_config()

    def save_wineexec(self):
        if not self.name in self.core.lgd.config.sections():
            self.core.lgd.config[self.name] = dict()
        self.core.lgd.config[self.name]["wine_executable"] = self.select_wine_exec.text()
        if self.select_wine_exec.text() == "":
            self.core.lgd.config[self.name].pop("wine_executable")
            logger.info("Remove wine executable section")
        else:
            logger.info("Set config of wine executable to " + self.select_wine_exec.text())
        if self.core.lgd.config[self.name] == {}:
            self.core.lgd.config.remove_section(self.name)
        self.core.lgd.save_config()
