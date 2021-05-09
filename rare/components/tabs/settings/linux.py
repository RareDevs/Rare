from logging import getLogger

from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QFileDialog, QLineEdit, QGroupBox

from custom_legendary.core import LegendaryCore
from rare.components.tabs.settings.dxvk import DxvkWidget
from rare.components.tabs.settings.settings_widget import SettingsWidget
from rare.utils.extra_widgets import PathEdit

logger = getLogger("LinuxSettings")


class LinuxSettings(QGroupBox):
    def __init__(self, core: LegendaryCore, name="default"):
        super(LinuxSettings, self).__init__()
        self.layout = QVBoxLayout()
        self.name = name
        self.core = core
        self.setTitle(self.tr("Linux settings"))
        self.setObjectName("group")
        # Wineprefix
        self.select_path = PathEdit(self.core.lgd.config.get(self.name, "wine_prefix", fallback=""),
                                    type_of_file=QFileDialog.DirectoryOnly,
                                    infotext="Default")
        self.select_path.text_edit.textChanged.connect(lambda t: self.save_path_button.setDisabled(False))
        self.save_path_button = QPushButton("Save")
        self.save_path_button.clicked.connect(lambda: self.save_setting(self.select_path, "wine_prefix"))
        self.install_dir_widget = SettingsWidget(self.tr("Default Wine Prefix"), self.select_path,
                                                 self.save_path_button)
        self.layout.addWidget(self.install_dir_widget)

        # Wine executable
        self.select_wine_exec = QLineEdit(self.core.lgd.config.get(self.name, "wine_executable", fallback=""))
        self.save_wine_exec = QPushButton("Save")
        self.save_wine_exec.clicked.connect(lambda: self.save_setting(self.select_wine_exec, "wine_executable"))
        self.install_dir_widget = SettingsWidget(self.tr("Default Wine executable"), self.select_wine_exec,
                                                 self.save_wine_exec)
        self.layout.addWidget(self.install_dir_widget)

        # dxvk
        self.dxvk_widget = DxvkWidget(core)
        self.layout.addWidget(self.dxvk_widget)
        if name == "default":
            self.layout.addStretch(1)
        self.setLayout(self.layout)

    def save_setting(self, widget: QLineEdit, setting_name: str):
        if not self.name in self.core.lgd.config.sections():
            self.core.lgd.config.add_section(self.name)

        self.core.lgd.config.set(self.name, setting_name, widget.text())
        if widget.text() == "":
            self.core.lgd.config.remove_option(self.name, setting_name)
        else:
            logger.info("Set config of wine_prefix to " + widget.text())
        if self.core.lgd.config[self.name] == {}:
            self.core.lgd.config.remove_section(self.name)
        self.core.lgd.save_config()
