import os
from getpass import getuser
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QFileDialog

from legendary.core import LegendaryCore
from rare.ui.components.dialogs.login.import_login import Ui_ImportLogin

logger = getLogger("ImportLogin")


class ImportLogin(QWidget, Ui_ImportLogin):
    success = pyqtSignal()
    changed = pyqtSignal()
    if os.name == "nt":
        localappdata = os.path.expandvars("%LOCALAPPDATA%")
    else:
        localappdata = os.path.join("drive_c/users", getuser(), "Local Settings/Application Data")
    appdata_path = os.path.join(localappdata, "EpicGamesLauncher/Saved/Config/Windows")
    found = False

    def __init__(self, core: LegendaryCore, parent=None):
        super(ImportLogin, self).__init__(parent=parent)
        self.setupUi(self)

        self.core = core

        self.text_egl_found = self.tr("Found EGL Program Data. Click 'Next' to import them.")
        self.text_egl_notfound = self.tr("Could not find EGL Program Data. ")

        if os.name == "nt":
            if not self.core.egl.appdata_path and os.path.exists(self.egl_data_path):
                self.core.egl.appdata_path = self.appdata_path
            if not self.core.egl.appdata_path:
                self.status_label.setText(self.text_egl_notfound)
            else:
                self.status_label.setText(self.text_egl_found)
                self.found = True
        else:
            self.info_label.setText(self.tr(
                "Please select the Wine prefix"
                " where Epic Games Launcher is installed. ") + self.info_label.text()
                                    )
            prefixes = self.get_wine_prefixes()
            if len(prefixes):
                self.prefix_combo.addItems(prefixes)
                self.status_label.setText(self.tr("Select the Wine prefix you want to import."))
            else:
                self.status_label.setText(self.text_egl_notfound)

        self.prefix_tool.clicked.connect(self.prefix_path)
        self.prefix_combo.editTextChanged.connect(self.changed.emit)

    def get_wine_prefixes(self):
        possible_prefixes = [
            os.path.expanduser("~/.wine"),
            os.path.expanduser("~/Games/epic-games-store"),
        ]
        prefixes = []
        for prefix in possible_prefixes:
            if os.path.exists(os.path.join(prefix, self.appdata_path)):
                prefixes.append(prefix)
        return prefixes

    def prefix_path(self):
        prefix_dialog = QFileDialog(self, self.tr("Choose path"), os.path.expanduser("~/"))
        prefix_dialog.setFileMode(QFileDialog.DirectoryOnly)
        if prefix_dialog.exec_():
            names = prefix_dialog.selectedFiles()
            self.prefix_combo.setCurrentText(names[0])

    def is_valid(self):
        if os.name == "nt":
            return self.found
        else:
            return os.path.exists(os.path.join(self.prefix_combo.currentText(), self.appdata_path))

    def do_login(self):
        self.status_label.setText(self.tr("Loading..."))
        if os.name == "nt":
            pass
        else:
            self.core.egl.appdata_path = os.path.join(self.prefix_combo.currentText(), self.appdata_path)
        try:
            if self.core.auth_import():
                logger.info(f"Logged in as {self.core.lgd.userdata['displayName']}")
                self.success.emit()
            else:
                self.status_label.setText(self.tr("Login failed."))
                logger.warning("Failed to import existing session.")
        except Exception as e:
            self.status_label.setText(self.tr("Login failed. ") + str(e))
            logger.warning("Failed to import existing session: " + str(e))
