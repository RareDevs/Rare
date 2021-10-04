from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QWidget, QMessageBox

from legendary.core import LegendaryCore
from legendary.models.game import Game
from rare.ui.components.tabs.games.game_info.game_dlc import Ui_GameDlc
from rare.ui.components.tabs.games.game_info.game_dlc_widget import Ui_GameDlcWidget
from rare.utils.models import Signals, InstallOptionsModel
from rare.utils.utils import get_pixmap


class GameDlc(QWidget, Ui_GameDlc):
    install_dlc = pyqtSignal(str, bool)
    game: Game

    def __init__(self, core: LegendaryCore, signals: Signals, parent=None):
        super(GameDlc, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = core
        self.signals = signals
        self.installed_dlcs = list()
        self.installed_dlc_widgets = list()
        self.available_dlc_widgets = list()

    def update_dlcs(self, app_name, dlcs: list):
        self.game = self.core.get_game(app_name)
        self.game_title.setText(f"<h4>{self.game.app_title}</h4>")

        if self.installed_dlc_widgets:
            for dlc_widget in self.installed_dlc_widgets:
                dlc_widget.deleteLater()
        self.installed_dlc_widgets.clear()
        if self.available_dlc_widgets:
            for dlc_widget in self.available_dlc_widgets:
                dlc_widget.install.disconnect()
                dlc_widget.deleteLater()
        self.available_dlc_widgets.clear()

        self.installed_dlcs = [i.app_name for i in self.core.get_installed_dlc_list()]
        for dlc in sorted(dlcs[self.game.asset_info.catalog_item_id], key=lambda x: x.app_title):
            if dlc.app_name in self.installed_dlcs:
                dlc_widget = GameDlcWidget(dlc, True)
                self.installed_dlc_widgets.append(dlc_widget)
                self.installed_dlc_group.layout().addWidget(dlc_widget)
            else:
                dlc_widget = GameDlcWidget(dlc, False)
                dlc_widget.install.connect(self.install)
                self.available_dlc_widgets.append(dlc_widget)
                self.available_dlc_group.layout().addWidget(dlc_widget)

        self.installed_dlc_label.setVisible(not self.installed_dlc_widgets)

        self.available_dlc_label.setVisible(not self.available_dlc_widgets)

    def install(self, app_name):
        if not self.core.is_installed(self.game.app_name):
            QMessageBox.warning(self, "Error", self.tr("Base Game is not installed. Please install {} first").format(
                self.game.app_title))
            return
        self.signals.dl_tab.emit((Signals.actions.install_game, InstallOptionsModel(app_name, update=True)))


class GameDlcWidget(QFrame, Ui_GameDlcWidget):
    install = pyqtSignal(str)  # Appname

    def __init__(self, dlc: Game, installed: bool, parent=None):
        super(GameDlcWidget, self).__init__(parent=parent)
        self.setupUi(self)
        self.dlc = dlc

        pixmap = get_pixmap(dlc.app_name)
        self.image.setPixmap(pixmap.scaledToHeight(pixmap.height() * 0.5))

        self.dlc_name.setText(dlc.app_title)
        self.version.setText(dlc.app_version)
        self.app_name.setText(dlc.app_name)

        if not installed:
            self.install_button.clicked.connect(lambda: self.install.emit(dlc.app_name))
            self.status.setText(self.tr("Not installed"))
        else:
            self.status.setText(self.tr("Installed. Uninstalling DLCs is not supported"))
        self.install_button.setVisible(not installed)

    def install_game(self):
        self.install_button.setDisabled(True)
        self.install_button.setText(self.tr("Installing"))
        self.install.emit(self.dlc.app_name)
