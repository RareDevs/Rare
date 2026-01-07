import os
import platform
from getpass import getuser

from legendary.lfs.wine_helpers import get_shell_folders, read_registry
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QFileDialog

from rare.lgndr.core import LegendaryCore
from rare.lgndr.glue.exception import LgndrException
from rare.ui.components.dialogs.login.import_login import Ui_ImportLogin

from .login_frame import LoginFrame


class ImportLogin(LoginFrame):

    # FIXME: Use pathspec instead of duplicated code
    if platform.system() == "Windows":
        localappdata = os.path.expandvars("%LOCALAPPDATA%")
    else:
        localappdata = os.path.join("drive_c/users", getuser(), "Local Settings/Application Data")
    egl_appdata = os.path.join(localappdata, "EpicGamesLauncher", "Saved", "Config", "Windows")
    found = False

    def __init__(self, core: LegendaryCore, parent=None):
        super(ImportLogin, self).__init__(core, parent=parent)

        self.ui = Ui_ImportLogin()
        self.ui.setupUi(self)

        self.text_egl_found = self.tr("Found EGL Program Data. Click 'Next' to import them.")
        self.text_egl_notfound = self.tr("Could not find EGL Program Data. ")

        if platform.system() == "Windows":
            if not self.core.egl.appdata_path and os.path.exists(self.egl_appdata):
                self.core.egl.appdata_path = self.egl_appdata
            if not self.core.egl.appdata_path:
                self.ui.status_field.setText(self.text_egl_notfound)
            else:
                self.ui.status_field.setText(self.text_egl_found)
                self.found = True
            self.ui.prefix_combo.setCurrentText(self.egl_appdata)
        else:
            if programdata_path := self.core.egl.programdata_path:
                if wine_pfx := programdata_path.split("drive_c")[0]:
                    self.ui.prefix_combo.addItem(wine_pfx)
            prefixes = self.get_wine_prefixes()
            if len(prefixes):
                self.ui.prefix_combo.addItems(prefixes)
                self.ui.status_field.setText(self.tr("Select the Wine prefix you want to import."))
            else:
                self.ui.status_field.setText(self.text_egl_notfound)

        self.ui.prefix_button.clicked.connect(self._on_prefix_path)
        self.ui.prefix_combo.editTextChanged.connect(self._on_input_changed)

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

    @Slot()
    def _on_prefix_path(self):
        prefix_dialog = QFileDialog(self, self.tr("Choose path"), os.path.expanduser("~/"))
        prefix_dialog.setFileMode(QFileDialog.FileMode.Directory)
        prefix_dialog.setOption(QFileDialog.Option.ShowDirsOnly)
        if prefix_dialog.exec_():
            names = prefix_dialog.selectedFiles()
            self.ui.prefix_combo.setCurrentText(names[0])

    def is_valid(self) -> bool:
        if platform.system() == "Windows":
            return self.found
        else:
            egl_wine_pfx = self.ui.prefix_combo.currentText()
            try:
                wine_folders = get_shell_folders(read_registry(egl_wine_pfx), egl_wine_pfx)
                self.egl_appdata = os.path.realpath(
                    os.path.join(wine_folders["Local AppData"], "EpicGamesLauncher", "Saved", "Config", "Windows")
                )
                if path_exists := os.path.exists(self.egl_appdata):
                    self.ui.status_field.setText(self.text_egl_found)
                return path_exists
            except KeyError:
                return False

    def do_login(self) -> None:
        self.ui.status_field.setText(self.tr("Loading..."))
        if os.name != "nt":
            self.logger.info("Using EGL appdata path at %s", {self.egl_appdata})
            self.core.egl.appdata_path = self.egl_appdata
        try:
            if self.core.auth_import():
                self.logger.info("Logged in as %s", {self.core.lgd.userdata["displayName"]})
                self.success.emit()
        except Exception as e:
            msg = e.message if isinstance(e, LgndrException) else str(e)
            self.ui.status_field.setText(self.tr("Login failed: {}").format(msg))
            self.logger.warning("Failed to import existing session")
            self.logger.error(e)
