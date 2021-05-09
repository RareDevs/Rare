from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QVBoxLayout, QFileDialog, QPushButton, QLineEdit, QGroupBox, QMessageBox, \
    QScrollArea

from custom_legendary.core import LegendaryCore
from rare.components.tabs.settings.settings_widget import SettingsWidget
from rare.utils.extra_widgets import PathEdit
from rare.utils.utils import get_size

logger = getLogger("LegendarySettings")


class LegendarySettings(QScrollArea):
    def __init__(self, core: LegendaryCore):
        super(LegendarySettings, self).__init__()
        self.widget = QGroupBox(self.tr("Legendary settings"))
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.layout = QVBoxLayout()
        self.core = core

        self.widget.setObjectName("group")
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

        # cleanup
        self.clean_layout = QVBoxLayout()
        self.cleanup_widget = QGroupBox(self.tr("Cleanup"))
        self.clean_button = QPushButton(self.tr("Remove everything"))
        self.clean_button.clicked.connect(lambda: self.cleanup(False))
        self.clean_layout.addWidget(self.clean_button)

        self.clean_button_without_manifests = QPushButton(self.tr("Clean, but keep manifests"))
        self.clean_button_without_manifests.clicked.connect(lambda: self.cleanup(True))
        self.clean_layout.addWidget(self.clean_button_without_manifests)

        self.cleanup_widget.setLayout(self.clean_layout)
        self.layout.addWidget(self.cleanup_widget)

        self.layout.addStretch(1)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def save_path(self):
        self.core.lgd.config["Legendary"]["install_dir"] = self.select_path.text()
        if self.select_path.text() == "" and "install_dir" in self.core.lgd.config["Legendary"].keys():
            self.core.lgd.config["Legendary"].pop("install_dir")
        else:
            logger.info("Set config install_dir to " + self.select_path.text())
        self.core.lgd.save_config()

    def max_worker_save(self, num_workers: str):
        if num_workers == "":
            self.core.lgd.config.remove_option("Legendary", "max_workers")
            self.core.lgd.save_config()
            return
        num_workers = int(num_workers)
        if num_workers == 0:
            self.core.lgd.config.remove_option("Legendary", "max_workers")
        else:
            self.core.lgd.config.set("Legendary", "max_workers", str(num_workers))
        self.core.lgd.save_config()

    def cleanup(self, keep_manifests):
        before = self.core.lgd.get_dir_size()
        logger.debug('Removing app metadata...')
        app_names = set(g.app_name for g in self.core.get_assets(update_assets=False))
        self.core.lgd.clean_metadata(app_names)

        if not keep_manifests:
            logger.debug('Removing manifests...')
            installed = [(ig.app_name, ig.version) for ig in self.core.get_installed_list()]
            installed.extend((ig.app_name, ig.version) for ig in self.core.get_installed_dlc_list())
            self.core.lgd.clean_manifests(installed)

        logger.debug('Removing tmp data')
        self.core.lgd.clean_tmp_data()

        after = self.core.lgd.get_dir_size()
        logger.info(f'Cleanup complete! Removed {(before - after) / 1024 / 1024:.02f} MiB.')
        if (before - after) > 0:
            QMessageBox.information(self, "Cleanup", self.tr("Cleanup complete! Successfully removed {}").format(
                get_size(before - after)))
        else:
            QMessageBox.information(self, "Cleanup", "Nothing to clean")
