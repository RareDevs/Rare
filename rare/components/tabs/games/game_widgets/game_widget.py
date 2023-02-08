import platform
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot, QObject, QEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QMessageBox, QAction

from rare.models.game import RareGame
from rare.shared import (
    LegendaryCoreSingleton,
    GlobalSignalsSingleton,
    ArgumentsSingleton,
    ImageManagerSingleton,
)
from rare.utils.paths import desktop_links_supported, desktop_link_path, create_desktop_link
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

        self.launch_action = QAction(self.tr("Launch"), self)
        self.launch_action.triggered.connect(self._launch)

        self.install_action = QAction(self.tr("Install"), self)
        self.install_action.triggered.connect(self._install)

        # self.sync_action = QAction(self.tr("Sync with cloud"), self)
        # self.sync_action.triggered.connect(self.sync_saves)

        self.desktop_link_action = QAction(self)
        self.desktop_link_action.triggered.connect(
            lambda: self._create_link(self.rgame.folder_name, "desktop")
        )

        self.menu_link_action = QAction(self)
        self.menu_link_action.triggered.connect(
            lambda: self._create_link(self.rgame.folder_name, "start_menu")
        )

        self.reload_action = QAction(self.tr("Reload Image"), self)
        self.reload_action.triggered.connect(self._on_reload_image)

        self.uninstall_action = QAction(self.tr("Uninstall"), self)
        self.uninstall_action.triggered.connect(self._uninstall)

        self.update_actions()

        # signals
        self.rgame.signals.widget.update.connect(lambda: self.setPixmap(self.rgame.pixmap))
        self.rgame.signals.widget.update.connect(self.update_buttons)
        self.rgame.signals.widget.update.connect(self.update_state)
        self.rgame.signals.game.installed.connect(self.update_actions)
        self.rgame.signals.game.uninstalled.connect(self.update_actions)

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

        self.state_strings = {
            RareGame.State.IDLE: "",
            RareGame.State.RUNNING: self.tr("Running..."),
            RareGame.State.DOWNLOADING: self.tr("Downloading..."),
            RareGame.State.VERIFYING: self.tr("Verifying..."),
            RareGame.State.MOVING: self.tr("Moving..."),
            RareGame.State.UNINSTALLING: self.tr("Uninstalling..."),
            RareGame.State.SYNCING: self.tr("Syncing saves..."),
            "has_update": self.tr("Update available"),
            "needs_verification": self.tr("Needs verification"),
            "not_can_launch": self.tr("Can't launch"),
            "save_not_up_to_date": self.tr("Save is not up-to-date")
        }

        self.hover_strings = {
            "info": self.tr("Show information"),
            "install": self.tr("Install game"),
            "can_launch": self.tr("Launch game"),
            "is_foreign": self.tr("Launch offline"),
            "has_update": self.tr("Launch without version check"),
            "is_origin": self.tr("Launch/Link"),
            "not_can_launch": self.tr("Can't launch"),
        }

    # lk: abstract class for typing, the `self.ui` attribute should be used
    # lk: by the Ui class in the children. It must contain at least the same
    # lk: attributes as `GameWidgetUi` class
    __slots__ = "ui"

    @pyqtSlot()
    def update_state(self):
        if self.rgame.is_idle:
            if self.rgame.has_update:
                self.ui.status_label.setText(self.state_strings["has_update"])
            elif self.rgame.needs_verification:
                self.ui.status_label.setText(self.state_strings["needs_verification"])
            elif not self.rgame.can_launch and self.rgame.is_installed:
                self.ui.status_label.setText(self.state_strings["not_can_launch"])
            elif self.rgame.igame and (
                    self.rgame.game.supports_cloud_saves or self.rgame.game.supports_mac_cloud_saves
            ) and not self.rgame.is_save_up_to_date:
                self.ui.status_label.setText(self.state_strings["save_not_up_to_date"])
            else:
                self.ui.status_label.setText(self.state_strings[self.rgame.state])
        else:
            self.ui.status_label.setText(self.state_strings[self.rgame.state])
        self.ui.status_label.setVisible(bool(self.ui.status_label.text()))

    @pyqtSlot()
    def update_buttons(self):
        self.ui.install_btn.setVisible(not self.rgame.is_installed)
        self.ui.install_btn.setEnabled(not self.rgame.is_installed)
        self.ui.launch_btn.setVisible(self.rgame.is_installed)
        self.ui.launch_btn.setEnabled(self.rgame.can_launch)

    @pyqtSlot()
    def update_actions(self):
        for action in self.actions():
            self.removeAction(action)

        if self.rgame.is_installed or self.rgame.is_origin:
            self.addAction(self.launch_action)
        else:
            self.addAction(self.install_action)

        # if self.rgame.game.supports_cloud_saves:
        #     self.addAction(self.sync_action)

        if desktop_links_supported() and self.rgame.is_installed:
            if desktop_link_path(self.rgame.folder_name, "desktop").exists():
                self.desktop_link_action.setText(self.tr("Remove Desktop link"))
            else:
                self.desktop_link_action.setText(self.tr("Create Desktop link"))
            self.addAction(self.desktop_link_action)
            if desktop_link_path(self.rgame.folder_name, "start_menu").exists():
                self.menu_link_action.setText(self.tr("Remove Start Menu link"))
            else:
                self.menu_link_action.setText(self.tr("Create Start Menu link"))
            self.addAction(self.menu_link_action)

        self.addAction(self.reload_action)
        if self.rgame.is_installed and not self.rgame.is_origin:
            self.addAction(self.uninstall_action)

    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        if a0 is self.ui.launch_btn:
            if a1.type() == QEvent.Enter:
                if not self.rgame.can_launch:
                    self.ui.tooltip_label.setText(self.hover_strings["not_can_launch"])
                elif self.rgame.is_origin:
                    self.ui.tooltip_label.setText(self.hover_strings["is_origin"])
                elif self.rgame.has_update:
                    self.ui.tooltip_label.setText(self.hover_strings["has_update"])
                elif self.rgame.is_foreign and self.rgame.can_run_offline:
                    self.ui.tooltip_label.setText(self.hover_strings["is_foreign"])
                elif self.rgame.can_launch:
                    self.ui.tooltip_label.setText(self.hover_strings["can_launch"])
                return True
            if a1.type() == QEvent.Leave:
                self.ui.tooltip_label.setText(self.hover_strings["info"])
                # return True
        if a0 is self.ui.install_btn:
            if a1.type() == QEvent.Enter:
                self.ui.tooltip_label.setText(self.hover_strings["install"])
                return True
            if a1.type() == QEvent.Leave:
                self.ui.tooltip_label.setText(self.hover_strings["info"])
                # return True
        if a0 is self:
            if a1.type() == QEvent.Enter:
                self.ui.tooltip_label.setText(self.hover_strings["info"])
        return super(GameWidget, self).eventFilter(a0, a1)

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

    def _create_link(self, name, link_type):
        if not desktop_links_supported():
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("Creating shortcuts is currently unsupported on {}").format(platform.system()),
            )
            return

        shortcut_path = desktop_link_path(name, link_type)

        if not shortcut_path.exists():
            try:
                if not create_desktop_link(
                    app_name=self.rgame.app_name,
                    app_title=self.rgame.app_title,
                    link_name=self.rgame.folder_name,
                    link_type=link_type,
                ):
                    raise PermissionError
            except PermissionError:
                QMessageBox.warning(self, "Error", "Could not create shortcut.")
                return

            if link_type == "desktop":
                self.desktop_link_action.setText(self.tr("Remove Desktop link"))
            elif link_type == "start_menu":
                self.menu_link_action.setText(self.tr("Remove Start Menu link"))
        else:
            if shortcut_path.exists():
                shortcut_path.unlink(missing_ok=True)

            if link_type == "desktop":
                self.desktop_link_action.setText(self.tr("Create Desktop link"))
            elif link_type == "start_menu":
                self.menu_link_action.setText(self.tr("Create Start Menu link"))

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
