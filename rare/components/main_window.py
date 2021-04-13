import platform
import time
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from custom_legendary.core import LegendaryCore
from rare.components.tab_widget import TabWidget
from rare.utils.rpc import DiscordRPC


class MainWindow(QMainWindow):

    def __init__(self, core: LegendaryCore):
        super(MainWindow, self).__init__()
        self.settings = QSettings()
        self.core = core
        self.rpc = DiscordRPC(core)
        width, height = 1200, 800
        if self.settings.value("save_size", False):
            width, height = self.settings.value("window_size", (1200, 800), tuple)

        self.setGeometry(0, 0, width, height)
        self.setWindowTitle("Rare - GUI for legendary")
        self.tab_widget = TabWidget(core)
        self.setCentralWidget(self.tab_widget)

        # Discord RPC on game launch
        self.tab_widget.games_tab.default_widget.game_list.game_started.connect(
            lambda: self.rpc.set_discord_rpc(self.tab_widget.games_tab.default_widget.game_list.running_games[0]))
        # Remove RPC
        self.tab_widget.delete_presence.connect(self.rpc.set_discord_rpc)
        # Show RPC on changed rare_settings
        self.tab_widget.settings.rare_settings.rpc.update_settings.connect(lambda: self.rpc.changed_settings(self.tab_widget.games_tab.default_widget.game_list.running_games))

        game = self.tab_widget.games_tab.default_widget.game_list.active_game
        if game != ("", 0):
            self.set_discord_rpc(game[0])  # Appname

        self.show()

    def closeEvent(self, e: QCloseEvent):
        if self.settings.value("sys_tray", True, bool):
            self.hide()
            e.ignore()
            return
        elif self.tab_widget.downloadTab.active_game is not None:
            if not QMessageBox.question(self, "Close", self.tr("There is a download active. Do you really want to exit app?"), QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                e.ignore()
                return
        if self.settings.value("save_size", False, bool):
            size = self.size().width(), self.size().height()
            self.settings.setValue("window_size", size)
        e.accept()

