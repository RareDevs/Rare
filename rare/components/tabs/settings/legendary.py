import os.path
import platform
import re
from logging import getLogger

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QVBoxLayout, QDialog, QCheckBox, QLabel, \
    QHBoxLayout, QPushButton, QGroupBox, QWidget
from qtawesome import icon

from legendary.core import LegendaryCore
from rare.ui.components.tabs.settings.legendary import Ui_LegendarySettings
from rare.utils.extra_widgets import PathEdit
from rare.utils.utils import get_size

logger = getLogger("LegendarySettings")


class LegendarySettings(QWidget, Ui_LegendarySettings):
    def __init__(self, core: LegendaryCore, parent=None):
        super(LegendarySettings, self).__init__(parent=parent)
        self.setupUi(self)

        self.core = core

        # Default installation directory
        self.install_dir = PathEdit(core.get_default_install_dir(),
                                    file_type=QFileDialog.DirectoryOnly,
                                    save_func=self.save_path)
        self.install_dir_layout.addWidget(self.install_dir)

        # Max Workers
        max_workers = self.core.lgd.config['Legendary'].getint('max_workers', fallback=0)
        self.max_worker_spin.setValue(max_workers)
        self.max_worker_spin.valueChanged.connect(self.max_worker_save)
        # Max memory
        max_memory = self.core.lgd.config['Legendary'].getint('max_memory', fallback=0)
        self.max_memory_spin.setValue(max_memory)
        self.max_memory_spin.valueChanged.connect(self.max_memory_save)
        # Preferred CDN
        preferred_cdn = self.core.lgd.config['Legendary'].get('preferred_cdn', fallback="")
        self.preferred_cdn_line.setText(preferred_cdn)
        self.preferred_cdn_line.textChanged.connect(self.preferred_cdn_save)
        # Disable HTTPS
        disable_https = self.core.lgd.config['Legendary'].getboolean('disable_https', fallback=False)
        self.disable_https_check.setChecked(disable_https)
        self.disable_https_check.stateChanged.connect(self.disable_https_save)

        # Cleanup
        self.clean_button.clicked.connect(
            lambda: self.cleanup(False)
        )
        self.clean_keep_manifests_button.clicked.connect(
            lambda: self.cleanup(True)
        )

        self.manifest_path_info.setText(self.tr("EGL path is at C:\\ProgramData\\Epic\\EpicGamesLauncher\\Data\\Manifests"))
        path = os.path.expanduser("~/")
        if self.core.egl.programdata_path:
            path = self.core.egl.programdata_path
        else:
            possible_wine_prefixes = [os.path.expanduser("~/.wine"),
                                      os.path.expanduser("~/Games/epic-games-store")]
            for i in possible_wine_prefixes:
                if os.path.exists(p := os.path.join(i, "drive_c/ProgramData/Epic/EpicGamesLauncher/Data/Manifests")):
                    path = p

        self.manifest_path_edit = PathEdit(path, QFileDialog.DirectoryOnly, save_func=self.save_egl_path)
        self.manifest_path_layout.addWidget(self.manifest_path_edit)
        if platform.system() != "Windows":
            self.core.lgd.config.set('Legendary', 'egl_programdata', path)
            self.core.egl.programdata_path = path

        self.importable_widgets = list()
        self.exportable_widgets = list()

        if self.core.egl_sync_enabled:
            self.egl_sync_button.setText(self.tr("Disable sync"))
        else:
            self.egl_sync_button.setText(self.tr("Enable Sync"))

        self.egl_sync_button.clicked.connect(self.sync)

        self.enable_sync_button.clicked.connect(self.enable_sync)
        self.sync_once_button.clicked.connect(self.core.egl_sync)

        self.locale_lineedit.setText(self.core.lgd.config.get("Legendary", "locale"))

        self.locale_lineedit.textChanged.connect(self.save_locale)

    def save_locale(self, text):
        if re.match("^[a-z]{2}-[A-Z]{2}$", text):
            self.core.egs.language_code = text[:2]
            self.core.egs.country_code = text[-2:]
            self.core.lgd.config.set("Legendary", "locale", text)
            self.core.lgd.save_config()
            self.indicator_label.setPixmap(icon("ei.ok-sign", color="green").pixmap(16, 16))
        elif re.match("^[a-zA-Z]{2}[-_][a-zA-Z]{2}$", text):
            self.locale_lineedit.setText(text[:2].lower() + "-" + text[-2:].upper())
        else:
            self.indicator_label.setPixmap(icon("fa.warning", color="red").pixmap(16, 16))

    def enable_sync(self):
        if not self.core.egl.programdata_path:
            if os.path.exists(path := self.manifest_path_edit.text()):
                self.core.lgd.config.set("Legendary", "egl_programdata", path)
                self.core.lgd.save_config()
                self.core.egl.programdata_path = path

        self.core.lgd.config.set('Legendary', 'egl_sync', "true")
        self.core.egl_sync()
        self.core.lgd.save_config()
        self.egl_sync_button.setText(self.tr("Disable Sync"))
        self.enable_sync_button.setDisabled(True)

    def export_all(self):
        for ew in self.exportable_widgets:
            ew.export_game()
        self.exportable_widgets.clear()

    def import_all(self):
        for iw in self.importable_widgets:
            iw.import_game()
        self.importable_widgets.clear()

    def save_egl_path(self):
        self.core.lgd.config.set("Legendary", "egl_programdata", self.manifest_path_edit.text())
        self.core.egl.programdata_path = self.manifest_path_edit.text()
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
                self.egl_sync_button.setText(self.tr("Enable Sync"))
        else:
            # enable sync
            self.enable_sync_button.setDisabled(False)
            self.update_egl_widget()

    def update_egl_widget(self):
        self.import_scroll.setVisible(bool(self.core.egl.programdata_path))
        self.export_scroll.setVisible(bool(self.core.egl.programdata_path))
        self.export_all_button.setDisabled(not bool(self.core.egl.programdata_path))
        self.import_all_button.setDisabled(not bool(self.core.egl.programdata_path))

        if not self.core.egl.programdata_path:
            return

        if self.exportable_widgets:
            for ew in self.exportable_widgets:
                # FIXME: Handle this using signals to properly update the list on python's side
                try:
                    ew.deleteLater()
                except RuntimeError as e:
                    print(e)
        self.exportable_widgets.clear()
        exportable_games = self.core.egl_get_exportable()
        for igame in exportable_games:
            ew = EGLSyncWidget(igame, True, self.core)
            self.exportable_widgets.append(ew)
            self.exportable_layout.addWidget(ew)
        self.export_group.setEnabled(bool(exportable_games))
        self.export_all_button.setEnabled(bool(exportable_games))
        self.export_label.setVisible(not bool(exportable_games))

        if self.importable_widgets:
            for iw in self.importable_widgets:
                # FIXME: Handle this using signals to properly update the list on python's side
                try:
                    iw.deleteLater()
                except RuntimeError as e:
                    print(e)
        self.importable_widgets.clear()
        importable_games = self.core.egl_get_importable()
        for game in importable_games:
            iw = EGLSyncWidget(game, False, self.core)
            self.importable_widgets.append(iw)
            self.importable_layout.addWidget(iw)
        self.import_group.setEnabled(bool(importable_games))
        self.import_all_button.setEnabled(bool(importable_games))
        self.import_label.setVisible(not bool(importable_games))

    def save_path(self):
        self.core.lgd.config["Legendary"]["install_dir"] = self.install_dir.text()
        if self.install_dir.text() == "" and "install_dir" in self.core.lgd.config["Legendary"].keys():
            self.core.lgd.config["Legendary"].pop("install_dir")
        else:
            logger.info("Set config install_dir to " + self.install_dir.text())
        self.core.lgd.save_config()

    def max_worker_save(self, workers: str):
        if workers := int(workers):
            self.core.lgd.config.set("Legendary", "max_workers", str(workers))
        else:
            self.core.lgd.config.remove_option("Legendary", "max_workers")
        self.core.lgd.save_config()

    def max_memory_save(self, memory: str):
        if memory := int(memory):
            self.core.lgd.config.set("Legendary", "max_memory", str(memory))
        else:
            self.core.lgd.config.remove_option("Legendary", "max_memory")
        self.core.lgd.save_config()

    def preferred_cdn_save(self, cdn: str):
        if cdn:
            self.core.lgd.config.set("Legendary", "preferred_cdn", cdn.strip())
        else:
            self.core.lgd.config.remove_option("Legendary", "preferred_cdn")
        self.core.lgd.save_config()

    def disable_https_save(self, checked: int):
        self.core.lgd.config.set("Legendary", "disable_https", str(bool(checked)).lower())
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

    def __init__(self, parent=None):
        super(DisableSyncDialog, self).__init__(parent=parent)
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
    def __init__(self, game, export: bool, core: LegendaryCore, parent=None):
        super(EGLSyncWidget, self).__init__(parent=parent)
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
        # FIXME: on update_egl_widget this is going to crash because
        # FIXME: the item is not removed from the list in the python's side
        self.deleteLater()

    def import_game(self):
        self.core.egl_import(self.game.app_name)
        # FIXME: on update_egl_widget this is going to crash because
        # FIXME: the item is not removed from the list in the python's side
        self.deleteLater()
