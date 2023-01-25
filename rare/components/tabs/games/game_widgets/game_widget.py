import os
import platform
from abc import abstractmethod
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QStandardPaths, Qt, pyqtSlot
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QMessageBox, QAction, QLabel, QPushButton

from rare.models.game import RareGame
from rare.shared import (
    LegendaryCoreSingleton,
    GlobalSignalsSingleton,
    ArgumentsSingleton,
    ImageManagerSingleton,
)
from rare.utils.misc import create_desktop_link
from .library_widget import LibraryWidget

logger = getLogger("GameWidget")


class GameWidget(LibraryWidget):
    show_info = pyqtSignal(RareGame)

    def __init__(self, rgame: RareGame, parent=None):
        super(GameWidget, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()
        self.image_manager = ImageManagerSingleton()

        self.rgame: RareGame = rgame

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        if self.rgame.is_installed or self.rgame.is_origin:
            self.launch_action = QAction(self.tr("Launch"), self)
            self.launch_action.triggered.connect(self._launch)
            self.addAction(self.launch_action)
        else:
            self.install_action = QAction(self.tr("Install"), self)
            self.install_action.triggered.connect(self._install)
            self.addAction(self.install_action)

        # if self.rgame.game.supports_cloud_saves:
        #     sync = QAction(self.tr("Sync with cloud"), self)
        #     sync.triggered.connect(self.sync_game)
        #     self.addAction(sync)

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
        reload_image.triggered.connect(self._on_reload_image)
        self.addAction(reload_image)

        if self.rgame.is_installed and not self.rgame.is_origin:
            self.uninstall_action = QAction(self.tr("Uninstall"), self)
            self.uninstall_action.triggered.connect(self._uninstall)
            self.addAction(self.uninstall_action)

        self.texts = {
            "hover": {
                "update_available": self.tr("Start without version check"),
                "launch": self.tr("Launch Game"),
                "launch_origin": self.tr("Launch/Link"),
                "running": self.tr("Game running"),
                "launch_offline": self.tr("Launch offline"),
                "no_launch": self.tr("Can't launch game")
            },
            "status": {
                "needs_verification": self.tr("Please verify game before playing"),
                "running": self.tr("Game running"),
                "syncing": self.tr("Syncing cloud saves"),
                "update_available": self.tr("Update available"),
                "no_meta": self.tr("Game is only offline available"),
                "no_launch": self.tr("Can't launch game"),
            },
        }

        # signals
        self.rgame.signals.widget.update.connect(
            lambda: self.setPixmap(self.rgame.pixmap)
        )
        self.rgame.signals.widget.update.connect(
            self.update_widget
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
        self.rgame.signals.progress.finish.connect(self.set_status)

    @abstractmethod
    def set_status(self, label: QLabel):
        if self.rgame.is_installed:
            if self.rgame.has_update:
                label.setText(self.texts["status"]["update_available"])
                return
            if self.rgame.needs_verification:
                label.setText(self.texts["status"]["needs_verification"])
                return
        label.setText("")
        label.setVisible(False)

    @abstractmethod
    def update_widget(self, install_btn: QPushButton, launch_btn: QPushButton):
        install_btn.setVisible(not self.rgame.is_installed)
        install_btn.setEnabled(not self.rgame.is_installed)
        launch_btn.setVisible(self.rgame.is_installed)
        launch_btn.setEnabled(self.rgame.can_launch)

    @property
    def enterEventText(self) -> str:
        if self.rgame.is_installed:
            if self.rgame.state == RareGame.State.RUNNING:
                return self.texts["status"]["running"]
            elif (not self.rgame.is_origin) and self.rgame.needs_verification:
                return self.texts["status"]["needs_verification"]
            elif self.rgame.is_foreign:
                return self.texts["hover"]["launch_offline"]
            elif self.rgame.has_update:
                return self.texts["hover"]["update_available"]
            else:
                return self.tr("Game Info")
                # return self.texts["hover"]["launch" if self.igame else "launch_origin"]
        else:
            if not self.rgame.state == RareGame.State.DOWNLOADING:
                return self.tr("Game Info")
            else:
                return self.tr("Installation running")

    @property
    def leaveEventText(self) -> str:
        if self.rgame.is_installed:
            if self.rgame.state == RareGame.State.RUNNING:
                return self.texts["status"]["running"]
            # elif self.syncing_cloud_saves:
            #     return self.texts["status"]["syncing"]
            elif self.rgame.is_foreign:
                return self.texts["status"]["no_meta"]
            elif self.rgame.has_update:
                return self.texts["status"]["update_available"]
            elif (not self.rgame.is_origin) and self.rgame.needs_verification:
                return self.texts["status"]["needs_verification"]
            else:
                return ""
        else:
            if self.rgame.state == RareGame.State.DOWNLOADING:
                return "Installation..."
            else:
                return ""

    def mousePressEvent(self, e: QMouseEvent) -> None:
        # left button
        if e.button() == 1:
            self.show_info.emit(self.rgame)
        # right
        elif e.button() == 2:
            super(GameWidget, self).mousePressEvent(e)

    @pyqtSlot()
    def _on_reload_image(self) -> None:
        self.rgame.refresh_pixmap()

    @pyqtSlot()
    @pyqtSlot(bool, bool)
    def _launch(self, offline=False, skip_version_check=False):
        if offline or (self.rgame.is_foreign and self.rgame.can_run_offline):
            offline = True
        # if self.rgame.game.supports_cloud_saves and not offline:
        #     self.syncing_cloud_saves = True
        if self.rgame.has_update:
            skip_version_check = True
        self.rgame.launch(
            offline=offline, skip_update_check=skip_version_check
        )

    @pyqtSlot()
    def _install(self):
        self.show_info.emit(self.rgame)

    @pyqtSlot()
    def _uninstall(self):
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

    # def sync_finished(self, app_name):
    #     self.syncing_cloud_saves = False

    # def sync_game(self):
    #     try:
    #         sync = self.game_utils.cloud_save_utils.sync_before_launch_game(
    #             self.rgame.app_name, True
    #         )
    #     except Exception:
    #         sync = False
    #     if sync:
    #         self.syncing_cloud_saves = True

    # def game_finished(self, app_name, error):
    #     if error:
    #         QMessageBox.warning(self, "Error", error)
    #     self.game_running = False
