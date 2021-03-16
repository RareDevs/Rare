from logging import getLogger

from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog, QPushButton, QLineEdit
from custom_legendary.core import LegendaryCore

from Rare.Components.Tabs.Settings.SettingsWidget import SettingsWidget
from Rare.utils.QtExtensions import PathEdit

logger = getLogger("LegendarySettings")


class LegendarySettings(QWidget):
    def __init__(self, core: LegendaryCore):
        super(LegendarySettings, self).__init__()
        self.layout = QVBoxLayout()
        self.core = core
        self.title = QLabel("<h2>"+self.tr("Legendary settings")+"</h2>")
        self.layout.addWidget(self.title)

        # Default installation directory
        self.select_path = PathEdit(core.get_default_install_dir(), type_of_file=QFileDialog.DirectoryOnly,
                                    infotext="Default")
        self.select_path.text_edit.textChanged.connect(lambda t: self.save_path_button.setDisabled(False))
        self.save_path_button = QPushButton("Save")
        self.save_path_button.clicked.connect(self.save_path)
        self.install_dir_widget = SettingsWidget(self.tr("Default installation directory"), self.select_path,
                                                 self.save_path_button)
        self.layout.addWidget(self.install_dir_widget)

        # Max Workers
        self.max_worker_select = QLineEdit(self.core.lgd.config["Legendary"].get("max_workers"))
        self.max_worker_select.setValidator(QIntValidator())
        self.max_worker_select.setPlaceholderText("Default")
        self.max_worker_select.textChanged.connect(self.max_worker_save)
        self.max_worker_widget = SettingsWidget(self.tr("Max workers for Download (Less: slower download)(0: Default)"),
                                                self.max_worker_select)
        self.layout.addWidget(self.max_worker_widget)

        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def save_path(self):
        self.core.lgd.config["Legendary"]["install_dir"] = self.select_path.text()
        if self.select_path.text() == "" and "install_dir" in self.core.lgd.config["Legendary"].keys():
            self.core.lgd.config["Legendary"].pop("install_dir")
            logger.info("Remove install_dir section")
        else:
            logger.info("Set config install_dir to " + self.select_path.text())
        self.core.lgd.save_config()

    def max_worker_save(self, num_workers: str):
        self.core.lgd.config["Legendary"]["max_workers"] = num_workers
        if num_workers == "":
            self.core.lgd.config["Legendary"].pop("max_workers")
            return
        num_workers = int(num_workers)
        if num_workers == 0:
            self.core.lgd.config["Legendary"].pop("max_workers")
        logger.info("Updating config for max_workers")
        self.core.lgd.save_config()
