import os
import platform
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QProcess, QSettings, QStandardPaths, Qt, QByteArray
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QMessageBox, QAction

from rare.components.tabs.games.game_utils import GameUtils
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton, ArgumentsSingleton, ImageManagerSingleton
from rare.shared.image_manager import ImageSize
from rare.utils.misc import create_desktop_link
from rare.widgets.image_widget import ImageWidget

logger = getLogger("Game")


class BaseInstalledWidget(QFrame):
    launch_signal = pyqtSignal(str, QProcess, list)
    show_info = pyqtSignal(str)
    finish_signal = pyqtSignal(str, int)
    proc: QProcess()

    def __init__(self, app_name, pixmap: QPixmap, game_utils: GameUtils):
        super(BaseInstalledWidget, self).__init__()
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()
        self.image_manager = ImageManagerSingleton()
        self.game_utils = game_utils

        self.syncing_cloud_saves = False

        self.texts = {
            "needs_verification": self.tr("Please verify game before playing"),
            "hover": {
                "update_available": self.tr("Start game without version check"),
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

        self.game = self.core.get_game(app_name)
        self.igame = self.core.get_installed_game(app_name)  # None if origin

        if self.game.app_title == "Unreal Engine":
            self.game.app_title = f"{self.game.app_title} {self.game.app_name.split('_')[-1]}"

        self.is_only_offline = False

        try:
            self.core.get_asset(app_name, platform=self.igame.platform).build_version
        except ValueError:
            logger.warning(f"Game {self.game.app_title} has no metadata. Set offline true")
            self.is_only_offline = True
        except AttributeError:
            pass

        self.image = ImageWidget(self)
        self.image.setFixedSize(ImageSize.Display)
        self.image.setPixmap(pixmap)
        self.game_running = False
        self.offline = self.args.offline
        self.update_available = False
        if self.igame and self.core.lgd.assets:
            try:
                remote_version = self.core.get_asset(
                    self.game.app_name, platform=self.igame.platform, update=False
                ).build_version
            except ValueError:
                logger.error(f"Asset error for {self.game.app_title}")
                self.update_available = False
            else:
                if remote_version != self.igame.version:
                    self.update_available = True

        self.data = QByteArray()
        self.settings = QSettings()

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        launch = QAction(self.tr("Launch"), self)
        launch.triggered.connect(self.launch)
        self.addAction(launch)

        if self.game.supports_cloud_saves:
            sync = QAction(self.tr("Sync with cloud"), self)
            sync.triggered.connect(self.sync_game)
            self.addAction(sync)

        desktop = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        if os.path.exists(
                os.path.join(desktop, f"{self.game.app_title}.desktop")
        ) or os.path.exists(os.path.join(desktop, f"{self.game.app_title}.lnk")):
            self.create_desktop = QAction(self.tr("Remove Desktop link"))
        else:
            self.create_desktop = QAction(self.tr("Create Desktop link"))
        if self.igame:
            self.create_desktop.triggered.connect(
                lambda: self.create_desktop_link("desktop")
            )
            self.addAction(self.create_desktop)

        applications = QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation)
        if platform.system() == "Linux":
            start_menu_file = os.path.join(applications, f"{self.game.app_title}.desktop")
        elif platform.system() == "Windows":
            start_menu_file = os.path.join(applications, "..", f"{self.game.app_title}.lnk")
        else:
            start_menu_file = ""
        if platform.system() in ["Windows", "Linux"]:
            if os.path.exists(start_menu_file):
                self.create_start_menu = QAction(self.tr("Remove start menu link"))
            else:
                self.create_start_menu = QAction(self.tr("Create start menu link"))
            if self.igame:
                self.create_start_menu.triggered.connect(
                    lambda: self.create_desktop_link("start_menu")
                )
                self.addAction(self.create_start_menu)

        reload_image = QAction(self.tr("Reload Image"), self)
        reload_image.triggered.connect(self.reload_image)
        self.addAction(reload_image)

        if self.igame is not None:
            uninstall = QAction(self.tr("Uninstall"), self)
            self.addAction(uninstall)
            uninstall.triggered.connect(
                lambda: self.signals.update_gamelist.emit([self.game.app_name])
                if self.game_utils.uninstall_game(self.game.app_name)
                else None
            )

    def reload_image(self):
        self.image_manager.download_image_blocking(self.game, force=True)
        pm = self.image_manager.get_pixmap(self.game.app_name, color=True)
        self.image.setPixmap(pm)

    def create_desktop_link(self, type_of_link):
        if type_of_link == "desktop":
            shortcut_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        elif type_of_link == "start_menu":
            shortcut_path = QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation)
        else:
            return

        if platform.system() == "Windows":
            shortcut_path = os.path.join(shortcut_path, f"{self.game.app_title}.lnk")
        elif platform.system() == "Linux":
            shortcut_path = os.path.join(shortcut_path, f"{self.game.app_title}.desktop")
        else:
            QMessageBox.warning(
                self,
                "Warning",
                f"Create a Desktop link is currently not supported on {platform.system()}",
            )
            return

        if not os.path.exists(shortcut_path):
            try:
                if not create_desktop_link(self.game.app_name, self.core, type_of_link):
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
        offline = offline or self.is_only_offline
        if self.is_only_offline and not self.igame.can_run_offline:
            QMessageBox.warning(self, "Warning",
                                self.tr("This game is probably not in your library and it cannot be launched offline"))
            return

        if self.game.supports_cloud_saves and not offline:
            self.syncing_cloud_saves = True
        self.game_utils.prepare_launch(
            self.game.app_name, offline, skip_version_check
        )

    def sync_finished(self, app_name):
        self.syncing_cloud_saves = False

    def sync_game(self):
        try:
            sync = self.game_utils.cloud_save_utils.sync_before_launch_game(
                self.game.app_name, True
            )
        except Exception:
            sync = False
        if sync:
            self.syncing_cloud_saves = True

    def game_finished(self, app_name, error):
        if error:
            QMessageBox.warning(self, "Error", error)
        self.game_running = False

    # From RareGame, added from sorting to work
    @property
    def is_non_asset(self) -> bool:
        """!
        @brief Property to report if a Game doesn't have assets

        Typically, games have assets, however some games that require
        other launchers do not have them. Rare treats these games as installed
        offering to execute their launcher.

        @return bool If the game doesn't have assets
        """
        return not self.game.asset_infos

    @property
    def is_origin(self) -> bool:
        return self.game.metadata.get("customAttributes", {}).get("ThirdPartyManagedApp", {}).get("value") == "Origin"

    @property
    def is_installed(self) -> bool:
        """!
        @brief Property to report if a game is installed

        This returns True if InstalledGame data have been loaded for the game
        or if the game is a game without assets, for example an Origin game.

        @return bool If the game should be considered installed
        """
        return (self.igame is not None) or self.is_non_asset

    @property
    def app_title(self) -> str:
        return self.igame.title if self.igame is not None else self.game.app_title
