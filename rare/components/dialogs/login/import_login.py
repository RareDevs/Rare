import os
from getpass import getuser
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QFileDialog
from legendary.core import LegendaryCore
from legendary.lfs.wine_helpers import get_shell_folders, read_registry

from rare.ui.components.dialogs.login.import_login import Ui_ImportLogin

logger = getLogger("ImportLogin")


class ImportLogin(QFrame):
    success = pyqtSignal()
    changed = pyqtSignal()
    if os.name == "nt":
        localappdata = os.path.expandvars("%LOCALAPPDATA%")
    else:
        localappdata = os.path.join("drive_c/users", getuser(), "Local Settings/Application Data")
    egl_appdata = os.path.join(localappdata, "EpicGamesLauncher", "Saved", "Config", "Windows")
    found = False

    def __init__(self, core: LegendaryCore, parent=None):
        super(ImportLogin, self).__init__(parent=parent)
        self.setFrameStyle(self.StyledPanel)
        self.ui = Ui_ImportLogin()
        self.ui.setupUi(self)

        self.core = core

        self.text_egl_found = self.tr("Found EGL Program Data. Click 'Next' to import them.")
        self.text_egl_notfound = self.tr("Could not find EGL Program Data. ")

        if os.name == "nt":
            if not self.core.egl.appdata_path and os.path.exists(self.egl_appdata):
                self.core.egl.appdata_path = self.egl_appdata
            if not self.core.egl.appdata_path:
                self.ui.status_label.setText(self.text_egl_notfound)
            else:
                self.ui.status_label.setText(self.text_egl_found)
                self.found = True
        else:
            if programdata_path := self.core.egl.programdata_path:
                if wine_pfx := programdata_path.split("drive_c")[0]:
                    self.ui.prefix_combo.addItem(wine_pfx)
            self.ui.info_label.setText(
                self.tr("Please select the Wine prefix where Epic Games Launcher is installed. ")
                + self.ui.info_label.text()
            )
            prefixes = self.get_wine_prefixes()
            if len(prefixes):
                self.ui.prefix_combo.addItems(prefixes)
                self.ui.status_label.setText(self.tr("Select the Wine prefix you want to import."))
            else:
                self.ui.status_label.setText(self.text_egl_notfound)

        self.ui.prefix_tool.clicked.connect(self.prefix_path)
        self.ui.prefix_combo.editTextChanged.connect(self.changed.emit)

    def get_wine_prefixes(self):
        possible_prefixes = [
            os.path.expanduser("~/.wine"),
            os.path.expanduser("~/Games/epic-games-store"),
        ]
        prefixes = []
        for prefix in possible_prefixes:
            if os.path.exists(os.path.join(prefix, self.egl_appdata)):
                prefixes.append(prefix)
        return prefixes

    def prefix_path(self):
        prefix_dialog = QFileDialog(self, self.tr("Choose path"), os.path.expanduser("~/"))
        prefix_dialog.setFileMode(QFileDialog.DirectoryOnly)
        if prefix_dialog.exec_():
            names = prefix_dialog.selectedFiles()
            self.ui.prefix_combo.setCurrentText(names[0])

    def is_valid(self) -> bool:
        if os.name == "nt":
            return self.found
        else:
            egl_wine_pfx = self.ui.prefix_combo.currentText()
            try:
                wine_folders = get_shell_folders(read_registry(egl_wine_pfx), egl_wine_pfx)
                self.egl_appdata = os.path.realpath(
                    os.path.join(wine_folders['Local AppData'], 'EpicGamesLauncher', 'Saved', 'Config', 'Windows'))
                if path_exists := os.path.exists(self.egl_appdata):
                    self.ui.status_label.setText(self.text_egl_found)
                return path_exists
            except KeyError:
                return False

    def do_login(self):
        self.ui.status_label.setText(self.tr("Loading..."))
        if os.name == "nt":
            pass
        else:
            logger.info(f'Using EGL appdata path at "{self.egl_appdata}"')
            self.core.egl.appdata_path = self.egl_appdata
        try:
            if self.core.auth_import():
                logger.info(f"Logged in as {self.core.lgd.userdata['displayName']}")
                self.success.emit()
            else:
                self.ui.status_label.setText(self.tr("Login failed."))
                logger.warning("Failed to import existing session.")
        except Exception as e:
            self.ui.status_label.setText(self.tr("Login failed. {}").format(str(e)))
            logger.warning(f"Failed to import existing session: {e}")
