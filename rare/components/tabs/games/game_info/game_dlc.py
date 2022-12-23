from typing import Optional

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QFrame, QWidget, QMessageBox
from legendary.models.game import Game

from rare.components.tabs.games.game_utils import GameUtils
from rare.models.install import InstallOptionsModel
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton, ImageManagerSingleton
from rare.shared.image_manager import ImageSize
from rare.ui.components.tabs.games.game_info.game_dlc import Ui_GameDlc
from rare.ui.components.tabs.games.game_info.game_dlc_widget import Ui_GameDlcWidget
from rare.widgets.image_widget import ImageWidget


class GameDlc(QWidget):
    install_dlc = pyqtSignal(str, bool)

    def __init__(self, dlcs: dict, game_utils: GameUtils, parent=None):
        super(GameDlc, self).__init__(parent=parent)
        self.ui = Ui_GameDlc()
        self.ui.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        self.game: Optional[Game] = None
        self.game_utils = game_utils

        self.ui.available_dlc_scroll.setFrameStyle(QFrame.NoFrame)
        self.ui.installed_dlc_scroll.setFrameStyle(QFrame.NoFrame)

        self.dlcs = dlcs
        self.installed_dlc_widgets = list()
        self.available_dlc_widgets = list()

    def update_dlcs(self, app_name):
        self.game = self.core.get_game(app_name)
        dlcs = self.dlcs[self.game.catalog_item_id]
        self.title.setTitle(self.game.app_title)

        if self.installed_dlc_widgets:
            for dlc_widget in self.installed_dlc_widgets:
                dlc_widget.uninstall.disconnect()
                dlc_widget.deleteLater()
        self.installed_dlc_widgets.clear()
        if self.available_dlc_widgets:
            for dlc_widget in self.available_dlc_widgets:
                dlc_widget.install.disconnect()
                dlc_widget.deleteLater()
        self.available_dlc_widgets.clear()

        for dlc in sorted(dlcs, key=lambda x: x.app_title):
            if self.core.is_installed(dlc.app_name):
                dlc_widget = GameDlcWidget(dlc, True)
                self.ui.installed_dlc_contents_layout.addWidget(dlc_widget)
                dlc_widget.uninstall.connect(self.uninstall)
                self.installed_dlc_widgets.append(dlc_widget)

            else:
                dlc_widget = GameDlcWidget(dlc, False)
                self.ui.available_dlc_contents_layout.addWidget(dlc_widget)
                dlc_widget.install.connect(self.install)
                self.available_dlc_widgets.append(dlc_widget)

        self.ui.installed_dlc_label.setVisible(not self.installed_dlc_widgets)
        self.ui.installed_dlc_scroll.setVisible(bool(self.installed_dlc_widgets))

        self.ui.available_dlc_label.setVisible(not self.available_dlc_widgets)
        self.ui.available_dlc_scroll.setVisible(bool(self.available_dlc_widgets))

    @pyqtSlot(str)
    def uninstall(self, app_name):
        if self.game_utils.uninstall_game(app_name):
            self.update_dlcs(self.game.app_name)

    def install(self, app_name):
        if not self.core.is_installed(self.game.app_name):
            QMessageBox.warning(
                self,
                "Error",
                self.tr("Base Game is not installed. Please install {} first").format(
                    self.game.app_title
                ),
            )
            return

        self.signals.install_game.emit(
            InstallOptionsModel(app_name=app_name, update=True)
        )


class GameDlcWidget(QFrame):
    install = pyqtSignal(str)  # Appname
    uninstall = pyqtSignal(str)

    def __init__(self, dlc: Game, installed: bool, parent=None):
        super(GameDlcWidget, self).__init__(parent=parent)
        self.image_manager = ImageManagerSingleton()
        self.ui = Ui_GameDlcWidget()
        self.ui.setupUi(self)
        self.dlc = dlc

        self.image = ImageWidget(self)
        self.image.setFixedSize(ImageSize.Smaller)
        self.ui.dlc_layout.insertWidget(0, self.image)

        self.ui.dlc_name.setText(dlc.app_title)
        self.ui.version.setText(dlc.app_version())
        self.ui.app_name.setText(dlc.app_name)

        self.image.setPixmap(self.image_manager.get_pixmap(dlc.app_name))

        if installed:
            self.ui.action_button.setProperty("uninstall", 1)
            self.ui.action_button.clicked.connect(self.uninstall_dlc)
            self.ui.action_button.setText(self.tr("Uninstall DLC"))
        else:
            self.ui.action_button.setProperty("install", 1)
            self.ui.action_button.clicked.connect(self.install_game)
            self.ui.action_button.setText(self.tr("Install DLC"))

    def uninstall_dlc(self):
        self.ui.action_button.setDisabled(True)
        self.ui.action_button.setText(self.tr("Uninstalling"))
        self.uninstall.emit(self.dlc.app_name)

    def install_game(self):
        self.ui.action_button.setDisabled(True)
        self.ui.action_button.setText(self.tr("Installing"))
        self.install.emit(self.dlc.app_name)
