import os
import platform
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QProcess, QSettings, Qt, QByteArray
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGroupBox, QMessageBox, QAction, QLabel

from rare import shared
from rare.components.tabs.games.game_utils import GameUtils
from rare.utils import utils
from rare.utils.utils import create_desktop_link

logger = getLogger("Game")


class BaseInstalledWidget(QGroupBox):
    launch_signal = pyqtSignal(str, QProcess, list)
    show_info = pyqtSignal(str)
    finish_signal = pyqtSignal(str, int)
    proc: QProcess()

    def __init__(self, app_name, pixmap: QPixmap, game_utils: GameUtils):
        super(BaseInstalledWidget, self).__init__()
        self.core = shared.core
        self.game_utils = game_utils

        self.syncing_cloud_saves = False

        self.texts = {
            "needs_verification": self.tr("Please verify game before playing"),
            "hover": {
                "update_available": self.tr("Start game without version check"),
                "launch": self.tr("Launch Game"),
                "launch_origin": self.tr("Launch/Link"),
                "running": self.tr("Game running")
            },
            "default": {
                "running": self.tr("Game running"),
                "syncing": self.tr("Syncing cloud saves"),
                "update_available": self.tr("Update available")
            }
        }

        self.game = self.core.get_game(app_name)
        if self.game.third_party_store != "Origin":
            self.igame = self.core.get_installed_game(app_name)
            self.is_origin = False
        else:
            self.igame = None
            self.is_origin = True

        self.image = QLabel()
        self.image.setPixmap(pixmap.scaled(200, int(200 * 4 / 3), transformMode=Qt.SmoothTransformation))
        self.game_running = False
        self.offline = shared.args.offline
        self.update_available = False
        if self.igame and self.core.lgd.assets:
            try:
                remote_version = self.core.get_asset(self.game.app_name, platform=self.igame.platform,
                                                     update=False).build_version
            except ValueError:
                logger.error("Asset error for " + self.game.app_title)
                self.update_available = False
            else:
                if remote_version != self.igame.version:
                    self.update_available = True

        self.data = QByteArray()
        self.setContentsMargins(0, 0, 0, 0)
        self.settings = QSettings()

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        launch = QAction(self.tr("Launch"), self)
        launch.triggered.connect(self.launch)
        self.addAction(launch)

        if self.game.supports_cloud_saves:
            sync = QAction(self.tr("Sync with cloud"), self)
            sync.triggered.connect(self.sync_game)
            self.addAction(sync)

        if os.path.exists(os.path.expanduser(f"~/Desktop/{self.game.app_title}.desktop")) \
                or os.path.exists(os.path.expanduser(f"~/Desktop/{self.game.app_title}.lnk")):
            self.create_desktop = QAction(self.tr("Remove Desktop link"))
        else:
            self.create_desktop = QAction(self.tr("Create Desktop link"))
        if not self.is_origin:
            self.create_desktop.triggered.connect(lambda: self.create_desktop_link("desktop"))
            self.addAction(self.create_desktop)

        if platform.system() == "Linux":
            start_menu_file = os.path.expanduser(f"~/.local/share/applications/{self.game.app_title}.desktop")
        elif platform.system() == "Windows":
            start_menu_file = os.path.expandvars("%appdata%/Microsoft/Windows/Start Menu")
        else:
            start_menu_file = ""
        if platform.system() in ["Windows", "Linux"]:
            if os.path.exists(start_menu_file):
                self.create_start_menu = QAction(self.tr("Remove start menu link"))
            else:
                self.create_start_menu = QAction(self.tr("Create start menu link"))
            if not self.is_origin:
                self.create_start_menu.triggered.connect(lambda: self.create_desktop_link("start_menu"))
                self.addAction(self.create_start_menu)

        reload_image = QAction(self.tr("Reload Image"), self)
        reload_image.triggered.connect(self.reload_image)
        self.addAction(reload_image)

        uninstall = QAction(self.tr("Uninstall"), self)
        uninstall.triggered.connect(
            lambda: shared.signals.update_gamelist.emit([self.game.app_name]) if self.game_utils.uninstall_game(
                self.game.app_name) else None)
        self.addAction(uninstall)

    def reload_image(self):
        utils.download_image(self.game, True)
        pm = utils.get_pixmap(self.game.app_name)
        self.image.setPixmap(pm.scaled(200, int(200 * 4 / 3), transformMode=Qt.SmoothTransformation))

    def create_desktop_link(self, type_of_link):
        if platform.system() not in ["Windows", "Linux"]:
            QMessageBox.warning(self, "Warning",
                                f"Create a Desktop link is currently not supported on {platform.system()}")
            return
        if type_of_link == "desktop":
            path = os.path.expanduser(f"~/Desktop/")
        elif type_of_link == "start_menu":
            path = os.path.expanduser("~/.local/share/applications/")
        else:
            return
        if not (os.path.exists(os.path.expanduser(f"{path}{self.game.app_title}.desktop"))
                or os.path.exists(os.path.expanduser(f"{path}{self.game.app_title}.lnk"))):
            try:
                if not create_desktop_link(self.game.app_name, self.core, type_of_link):
                    return
            except PermissionError:
                QMessageBox.warning(self, "Error", "Permission error. Cannot create Desktop Link")
            if type_of_link == "desktop":
                self.create_desktop.setText(self.tr("Remove Desktop link"))
            elif type_of_link == "start_menu":
                self.create_start_menu.setText(self.tr("Remove Start menu link"))
        else:
            if os.path.exists(os.path.expanduser(f"{path}{self.game.app_title}.desktop")):
                os.remove(os.path.expanduser(f"{path}{self.game.app_title}.desktop"))
            elif os.path.exists(os.path.expanduser(f"{path}{self.game.app_title}.lnk")):
                os.remove(os.path.expanduser(f"{path}{self.game.app_title}.lnk"))

            if type_of_link == "desktop":
                self.create_desktop.setText(self.tr("Create Desktop link"))
            elif type_of_link == "start_menu":
                self.create_start_menu.setText(self.tr("Create Start menu link"))

    def launch(self, offline=False, skip_version_check=False):
        if not self.game_running:
            if self.game.supports_cloud_saves:
                self.syncing_cloud_saves = True
            self.game_utils.prepare_launch(self.game.app_name, offline, skip_version_check)

    def sync_finished(self, app_name):
        self.syncing_cloud_saves = False

    def sync_game(self):

        if self.game_utils.cloud_save_utils.sync_before_launch_game(self.game.app_name, True):
            self.syncing_cloud_saves = True

    def game_finished(self, app_name, error):
        if error:
            QMessageBox.warning(self, "Error", error)
        self.game_running = False
