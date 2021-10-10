from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QWidget, QMessageBox

from legendary.models.game import Game
from rare import shared
from rare.components.dialogs.uninstall_dialog import UninstallDialog
from rare.ui.components.tabs.games.game_info.game_dlc import Ui_GameDlc
from rare.ui.components.tabs.games.game_info.game_dlc_widget import Ui_GameDlcWidget
from rare.utils import legendary_utils
from rare.utils.models import InstallOptionsModel
from rare.utils.utils import get_pixmap


class GameDlc(QWidget, Ui_GameDlc):
    install_dlc = pyqtSignal(str, bool)
    game: Game

    def __init__(self, dlcs: list, parent=None):
        super(GameDlc, self).__init__(parent=parent)
        self.setupUi(self)

        self.available_dlc_scroll.setObjectName("noborder")
        self.installed_dlc_scroll.setObjectName("noborder")
        self.signals = shared.signals
        self.core = shared.legendary_core

        self.dlcs = dlcs
        self.installed_dlc_widgets = list()
        self.available_dlc_widgets = list()

    def update_dlcs(self, app_name):
        self.game = self.core.get_game(app_name)
        dlcs = self.dlcs[self.game.asset_info.catalog_item_id]
        self.game_title.setText(f"<h2>{self.game.app_title}</h2>")

        if self.installed_dlc_widgets:
            for dlc_widget in self.installed_dlc_widgets:
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
                self.installed_dlc_contents_layout.addWidget(dlc_widget)
                dlc_widget.uninstall.connect(self.uninstall)
                self.installed_dlc_widgets.append(dlc_widget)

            else:
                dlc_widget = GameDlcWidget(dlc, False)
                self.available_dlc_contents_layout.addWidget(dlc_widget)
                dlc_widget.install.connect(self.install)
                self.available_dlc_widgets.append(dlc_widget)

        self.installed_dlc_label.setVisible(not self.installed_dlc_widgets)
        self.installed_dlc_scroll.setVisible(bool(self.installed_dlc_widgets))

        self.available_dlc_label.setVisible(not self.available_dlc_widgets)
        self.available_dlc_scroll.setVisible(bool(self.available_dlc_widgets))

    def uninstall(self, game):
        infos = UninstallDialog(game).get_information()
        if infos == 0:
            return
        legendary_utils.uninstall(game.app_name, self.core, infos)
        self.update_dlcs(self.game.app_name)

    def install(self, app_name):
        if not self.core.is_installed(self.game.app_name):
            QMessageBox.warning(self, "Error", self.tr("Base Game is not installed. Please install {} first").format(
                self.game.app_title))
            return

        self.signals.dl_tab.emit(
            (self.signals.actions.install_game, (InstallOptionsModel(app_name=app_name, update=True))))


class GameDlcWidget(QFrame, Ui_GameDlcWidget):
    install = pyqtSignal(str)  # Appname
    uninstall = pyqtSignal(Game)

    def __init__(self, dlc: Game, installed: bool, parent=None):
        super(GameDlcWidget, self).__init__(parent=parent)
        self.setupUi(self)
        self.dlc = dlc

        pixmap = get_pixmap(dlc.app_name)
        self.image.setPixmap(pixmap.scaledToHeight(pixmap.height() * 0.5))

        self.dlc_name.setText(dlc.app_title)
        self.version.setText(dlc.app_version)
        self.app_name.setText(dlc.app_name)

        if installed:
            self.install_button.clicked.connect(self.uninstall_dlc)
            self.status.setText(self.tr("Installed"))
            self.install_button.setText("Uninstall")

        else:
            self.install_button.clicked.connect(self.install_game)
            self.status.setText(self.tr("Not installed"))
            self.install_button.setText("Install")

    def uninstall_dlc(self):
        self.uninstall.emit(self.dlc)

    def install_game(self):
        self.install_button.setDisabled(True)
        self.install_button.setText(self.tr("Installing"))
        self.install.emit(self.dlc.app_name)
