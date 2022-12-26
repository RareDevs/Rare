import os
import platform
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QSettings, QStandardPaths, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QMessageBox, QAction

from rare.models.game import RareGame
from rare.shared import (
    LegendaryCoreSingleton,
    GlobalSignalsSingleton,
    ArgumentsSingleton,
    ImageManagerSingleton,
)
from rare.shared.game_utils import GameUtils
from rare.utils.misc import create_desktop_link
from .library_widget import LibraryWidget

logger = getLogger("BaseGameWidget")


class GameWidget(LibraryWidget):
    show_info = pyqtSignal(RareGame)

    def __init__(self, rgame: RareGame, game_utils: GameUtils, parent=None):
        super(GameWidget, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()
        self.image_manager = ImageManagerSingleton()

        self.game_utils = game_utils

        self.rgame = rgame
        self.rgame.signals.widget.update.connect(
            lambda: self.setPixmap(self.rgame.pixmap)
        )
        self.rgame.signals.progress.start.connect(
            lambda: self.showProgress(
                self.image_manager.get_pixmap(self.rgame.app_name, True),
                self.image_manager.get_pixmap(self.rgame.app_name, False)
            )
        )
        self.rgame.signals.progress.update.connect(
            lambda p: self.updateProgress(p)
        )
        self.rgame.signals.progress.finish.connect(
            lambda e: self.hideProgress(e)
        )

        self.rgame: RareGame = rgame
        self.syncing_cloud_saves = False

        self.game_running = False

        self.settings = QSettings()

        self.installing = False
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        launch = QAction(self.tr("Launch"), self)
        launch.triggered.connect(self.launch)
        self.addAction(launch)

        if self.rgame.game.supports_cloud_saves:
            sync = QAction(self.tr("Sync with cloud"), self)
            sync.triggered.connect(self.sync_game)
            self.addAction(sync)

        desktop = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        if os.path.exists(
                os.path.join(desktop, f"{self.rgame.app_title}.desktop")
        ) or os.path.exists(os.path.join(desktop, f"{self.rgame.app_title}.lnk")):
            self.create_desktop = QAction(self.tr("Remove Desktop link"))
        else:
            self.create_desktop = QAction(self.tr("Create Desktop link"))
        if self.rgame.is_installed:
            self.create_desktop.triggered.connect(
                lambda: self.create_desktop_link("desktop")
            )
            self.addAction(self.create_desktop)

        applications = QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation)
        if platform.system() == "Linux":
            start_menu_file = os.path.join(applications, f"{self.rgame.app_title}.desktop")
        elif platform.system() == "Windows":
            start_menu_file = os.path.join(applications, "..", f"{self.rgame.app_title}.lnk")
        else:
            start_menu_file = ""
        if platform.system() in ["Windows", "Linux"]:
            if os.path.exists(start_menu_file):
                self.create_start_menu = QAction(self.tr("Remove start menu link"))
            else:
                self.create_start_menu = QAction(self.tr("Create start menu link"))
            if self.rgame.is_installed:
                self.create_start_menu.triggered.connect(
                    lambda: self.create_desktop_link("start_menu")
                )
                self.addAction(self.create_start_menu)

        reload_image = QAction(self.tr("Reload Image"), self)
        reload_image.triggered.connect(self.reload_image)
        self.addAction(reload_image)

        if not self.rgame.is_origin:
            uninstall = QAction(self.tr("Uninstall"), self)
            self.addAction(uninstall)
            uninstall.triggered.connect(
                lambda: self.signals.game.uninstalled.emit(self.rgame.app_name)
                if self.game_utils.uninstall_game(self.rgame.app_name)
                else None
            )

        self.texts = {
            "static": {
                "needs_verification": self.tr("Please verify game before playing"),
            },
            "hover": {
                "update_available": self.tr("Start without version check"),
                "launch": self.tr("Launch Game"),
                "launch_origin": self.tr("Launch/Link"),
                "running": self.tr("Game running"),
                "launch_offline": self.tr("Launch offline"),
                "no_launch": self.tr("Can't launch game")
            },
            "default": {
                "running": self.tr("Game running"),
                "syncing": self.tr("Syncing cloud saves"),
                "update_available": self.tr("Update available"),
                "no_meta": self.tr("Game is only offline available")
            },
        }

    @property
    def enterEventText(self) -> str:
        if self.rgame.is_installed:
            if self.game_running:
                return self.texts["hover"]["running"]
            elif (not self.rgame.is_origin) and self.rgame.needs_verification:
                return self.texts["static"]["needs_verification"]
            elif self.rgame.is_foreign:
                return self.texts["hover"]["launch_offline"]
            elif self.rgame.has_update:
                return self.texts["hover"]["update_available"]
            else:
                return self.tr("Game Info")
                # return self.texts["hover"]["launch" if self.igame else "launch_origin"]
        else:
            if not self.installing:
                return self.tr("Game Info")
            else:
                return self.tr("Installation running")

    @property
    def leaveEventText(self) -> str:
        if self.rgame.is_installed:
            if self.game_running:
                return self.texts["default"]["running"]
            elif self.syncing_cloud_saves:
                return self.texts["default"]["syncing"]
            elif self.rgame.is_foreign:
                return self.texts["default"]["no_meta"]
            elif self.rgame.has_update:
                return self.texts["default"]["update_available"]
            elif (not self.rgame.is_origin) and self.rgame.needs_verification:
                return self.texts["static"]["needs_verification"]
            else:
                return ""
        else:
            if self.installing:
                return "Installation..."
            else:
                return ""

    def mousePressEvent(self, e: QMouseEvent) -> None:
        # left button
        if e.button() == 1:
            self.show_info.emit(self.rgame)
        # right
        elif e.button() == 2:
            pass  # self.showMenu(e)

    def reload_image(self) -> None:
        self.rgame.refresh_pixmap()

    def install(self):
        self.show_info.emit(self.rgame)

    def create_desktop_link(self, type_of_link):
        if type_of_link == "desktop":
            shortcut_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        elif type_of_link == "start_menu":
            shortcut_path = QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation)
        else:
            return

        if platform.system() == "Windows":
            shortcut_path = os.path.join(shortcut_path, f"{self.rgame.app_title}.lnk")
        elif platform.system() == "Linux":
            shortcut_path = os.path.join(shortcut_path, f"{self.rgame.app_title}.desktop")
        else:
            QMessageBox.warning(
                self,
                "Warning",
                f"Create a Desktop link is currently not supported on {platform.system()}",
            )
            return

        if not os.path.exists(shortcut_path):
            try:
                if not create_desktop_link(self.rgame.app_name, self.core, type_of_link):
                    return
            except PermissionError:
                QMessageBox.warning(
                    self, "Error", "Permission error. Cannot create Desktop Link"
                )
            if type_of_link == "desktop":
                self.create_desktop.setText(self.tr("Remove Desktop link"))
            elif type_of_link == "start_menu":
                self.create_start_menu.setText(self.tr("Remove Start menu link"))
        else:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)

            if type_of_link == "desktop":
                self.create_desktop.setText(self.tr("Create Desktop link"))
            elif type_of_link == "start_menu":
                self.create_start_menu.setText(self.tr("Create Start menu link"))

    def launch(self, offline=False, skip_version_check=False):
        if self.game_running:
            return
        offline = offline or self.rgame.is_foreign
        if self.rgame.is_foreign and not self.rgame.can_run_offline:
            QMessageBox.warning(self, "Warning",
                                self.tr("This game is probably not in your library and it cannot be launched offline"))
            return

        if self.rgame.game.supports_cloud_saves and not offline:
            self.syncing_cloud_saves = True
        self.game_utils.prepare_launch(
            self.rgame, offline, skip_version_check
        )

    def sync_finished(self, app_name):
        self.syncing_cloud_saves = False

    def sync_game(self):
        try:
            sync = self.game_utils.cloud_save_utils.sync_before_launch_game(
                self.rgame.app_name, True
            )
        except Exception:
            sync = False
        if sync:
            self.syncing_cloud_saves = True

    def game_finished(self, app_name, error):
        if error:
            QMessageBox.warning(self, "Error", error)
        self.game_running = False
