import os.path
import platform
from logging import getLogger

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QStackedWidget, QVBoxLayout, QDialog, QCheckBox, QLabel, \
    QHBoxLayout, QPushButton, QGroupBox, QWidget

from custom_legendary.core import LegendaryCore
from rare.ui.components.tabs.settings.legendary import Ui_legendary_settings
from rare.utils.extra_widgets import PathEdit
from rare.utils.utils import get_size

logger = getLogger("LegendarySettings")


class LegendarySettings(QStackedWidget, Ui_legendary_settings):
    def __init__(self, core: LegendaryCore):
        super(LegendarySettings, self).__init__()
        self.setupUi(self)

        self.core = core

        # Default installation directory
        self.install_dir = PathEdit(core.get_default_install_dir(),
                                    file_type=QFileDialog.DirectoryOnly,
                                    save_func=self.save_path)
        self.layout_install_dir.addWidget(self.install_dir)

        # Max Workers
        max_workers = self.core.lgd.config["Legendary"].get("max_workers", fallback=0)
        self.max_worker_select.setValue(int(max_workers))
        self.max_worker_select.valueChanged.connect(self.max_worker_save)

        # Cleanup
        self.clean_button.clicked.connect(
            lambda: self.cleanup(False)
        )
        self.clean_button_without_manifests.clicked.connect(
            lambda: self.cleanup(True)
        )
        self.setCurrentIndex(0)

        self.back_button.clicked.connect(lambda: self.setCurrentIndex(0))

        self.path_info.setText(self.tr("EGL path is at C:\\ProgramData\\Epic\\EpicGamesLauncher\\Data\\Manifests"))
        path = os.path.expanduser("~/")
        if self.core.egl.programdata_path:
            path = self.core.egl.programdata_path
        else:
            possible_wine_prefixes = [os.path.expanduser("~/.wine"),
                                      os.path.expanduser("~/Games/epic-games-store")]
            for i in possible_wine_prefixes:
                if os.path.exists(p := os.path.join(i, "drive_c/ProgramData/Epic/EpicGamesLauncher/Data/Manifests")):
                    path = p

        self.path_edit = PathEdit(path, QFileDialog.DirectoryOnly, save_func=self.save_egl_path)
        self.pathedit_placeholder.addWidget(self.path_edit)
        if platform.system() != "Windows":
            self.core.lgd.config.set("Legendary", "egl_programdata")
            self.core.egl.programdata_path = path

        self.importable_widgets = []
        self.exportable_widgets = []

        if self.core.egl_sync_enabled:
            self.sync_button.setText(self.tr("Disable sync"))
        else:
            self.sync_button.setText(self.tr("Enable Sync"))

        self.sync_button.clicked.connect(self.sync)

        self.enable_sync_button.clicked.connect(self.enable_sync)
        self.sync_once_button.clicked.connect(self.core.egl_sync)

    def enable_sync(self):
        if not self.core.egl.programdata_path:
            if os.path.exists(path := self.path_edit.text()):
                self.core.lgd.config.set("Legendary", "egl_programdata", path)
                self.core.lgd.save_config()
                self.core.egl.programdata_path = path

        self.core.lgd.config.set('Legendary', 'egl_sync', "true")
        self.core.egl_sync()
        self.core.lgd.save_config()
        self.sync_button.setText(self.tr("Disable Sync"))
        self.enable_sync_button.setDisabled(True)

    def export_all(self):
        for w in self.exportable_widgets:
            w.export_game()

    def import_all(self):
        for w in self.importable_widgets:
            w.import_game()

    def save_egl_path(self):
        self.core.lgd.config.set("Legendary", "egl_programdata", self.path_edit.text())
        self.core.egl.programdata_path = self.path_edit.text()
        self.core.lgd.save_config()
        self.update_egl_widget()

    def sync(self):
        if self.core.egl_sync_enabled:
            # disable sync
            info = DisableSyncDialog().get_information()
            if info[0] == 0:
                if info[1]:
                    self.core.lgd.config.remove_option('Legendary', 'egl_sync')
                else:
                    self.core.lgd.config.remove_option('Legendary', 'egl_programdata')
                    self.core.lgd.config.remove_option('Legendary', 'egl_sync')
                    # remove EGL GUIDs from all games, DO NOT remove .egstore folders because that would fuck things up.
                    for igame in self.core.get_installed_list():
                        igame.egl_guid = ''
                        self.core.install_game(igame)
                self.core.lgd.save_config()
                self.sync_button.setText(self.tr("Enable Sync"))
        else:
            # enable sync
            self.enable_sync_button.setDisabled(False)
            self.update_egl_widget()
            self.setCurrentIndex(1)

    def update_egl_widget(self):
        self.exportable_widgets = []
        QWidget().setLayout(self.exportable_games.layout())
        QWidget().setLayout(self.importable_games.layout())
        importable_layout = QVBoxLayout()
        self.importable_games.setLayout(importable_layout)
        exportable_layout = QVBoxLayout()
        self.exportable_games.setLayout(exportable_layout)
        if not self.core.egl.programdata_path:
            self.importable_games.setVisible(False)
            self.exportable_games.setVisible(False)
            self.export_all_button.setVisible(False)
            self.import_all_button.setVisible(False)
            return

        self.importable_games.setVisible(True)
        self.exportable_games.setVisible(True)
        self.export_all_button.setVisible(True)
        self.import_all_button.setVisible(True)

        for igame in self.core.egl_get_exportable():
            w = EGLSyncWidget(igame, True, self.core)
            self.importable_widgets.append(w)
            self.exportable_games.layout().addWidget(w)
        if len(self.core.egl_get_exportable()) == 0:
            self.exportable_games.layout().addWidget(QLabel(self.tr("No games to export")))

        self.importable_widgets = []
        for game in self.core.egl_get_importable():
            w = EGLSyncWidget(game, False, self.core)
            self.importable_widgets.append(w)
            self.importable_games.layout().addWidget(w)
        if len(self.core.egl_get_importable()) == 0:
            self.importable_games.layout().addWidget(QLabel(self.tr("No games to import")))

    def save_path(self):
        self.core.lgd.config["Legendary"]["install_dir"] = self.install_dir.text()
        if self.install_dir.text() == "" and "install_dir" in self.core.lgd.config["Legendary"].keys():
            self.core.lgd.config["Legendary"].pop("install_dir")
        else:
            logger.info("Set config install_dir to " + self.install_dir.text())
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


class DisableSyncDialog(QDialog):
    info = 1, False

    def __init__(self):
        super(DisableSyncDialog, self).__init__()
        self.layout = QVBoxLayout()

        self.question = QLabel(self.tr("Do you really want to disable sync with Epic Games Store"))
        self.layout.addWidget(self.question)

        self.remove_metadata = QCheckBox(self.tr("Remove metadata from installed games"))
        self.layout.addWidget(self.remove_metadata)

        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch(1)

        self.ok_button = QPushButton(self.tr("Ok"))
        self.cancel_button = QPushButton(self.tr("Cancel"))

        self.ok_button.clicked.connect(self.ok)
        self.cancel_button.clicked.connect(self.cancel)

        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)

        self.layout.addStretch(1)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def ok(self):
        self.info = 0, self.remove_metadata.isChecked()
        self.close()

    def cancel(self):
        self.close()

    def get_information(self):
        self.exec_()
        return self.info


class EGLSyncWidget(QGroupBox):
    def __init__(self, game, export: bool, core: LegendaryCore):
        super(EGLSyncWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.export = export
        self.core = core
        self.game = game
        if export:
            self.app_title_label = QLabel(game.title)
        else:
            title = self.core.get_game(game.app_name).app_title
            self.app_title_label = QLabel(title)
        self.layout.addWidget(self.app_title_label)
        self.button = QPushButton(self.tr("Export") if export else self.tr("Import"))

        if export:
            self.button.clicked.connect(self.export_game)
        else:
            self.button.clicked.connect(self.import_game)

        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

    def export_game(self):
        self.core.egl_export(self.game.app_name)

    def import_game(self):
        self.core.egl_import(self.game.app_name)
