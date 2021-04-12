import platform
import time
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from pypresence import Presence

from custom_legendary.core import LegendaryCore
from rare.components.tab_widget import TabWidget


class MainWindow(QMainWindow):

    def __init__(self, core: LegendaryCore):
        super(MainWindow, self).__init__()
        self.settings = QSettings()
        self.core = core
        width, height = 1200, 800
        if self.settings.value("save_size", False):
            width, height = self.settings.value("window_size", (1200, 800), tuple)

        self.setGeometry(0, 0, width, height)
        self.setWindowTitle("Rare - GUI for legendary")
        self.tab_widget = TabWidget(core)
        self.setCentralWidget(self.tab_widget)

        self.tab_widget.games_tab.default_widget.game_list.game_started.connect(self.set_discord_rpc)
        self.tab_widget.delete_presence.connect(self.remove_rpc)
        game = self.tab_widget.games_tab.default_widget.game_list.active_game
        if game != ("", 0):
            self.set_discord_rpc(game[0])  # Appname
        self.RPC = None
        if self.settings.value("rpc_enable", 0, int) == 1:  # show always
            self.RPC = Presence("830732538225360908")
            self.RPC.connect()
            self.update_rpc()
        self.show()

    def remove_rpc(self):
        if self.settings.value("rpc_enable", 0, int) != 1:
            if not self.RPC:
                return
            self.RPC.close()
            del self.RPC
            self.RPC = None
        else:
            self.update_rpc()

    def set_discord_rpc(self, app_name):
        if not self.RPC:
            self.RPC = Presence("830732538225360908")  # Rare app: https://discord.com/developers/applications
            self.RPC.connect()
        self.update_rpc(app_name)

    def update_rpc(self, app_name=None):
        if self.settings.value("rpc_enable", 0, int) == 2:
            self.remove_rpc()
            return
        title = None
        if not app_name:
            self.RPC.update(large_image="logo",
                            details="https://github.com/Dummerle/Rare")
            return
        if self.settings.value("rpc_name", True, bool):
            title = self.core.get_installed_game(app_name).title
        start = None
        if self.settings.value("rpc_time", True, bool):
            start = str(time.time()).split(".")[0]
        os = None
        if self.settings.value("rpc_os", True, bool):
            os = "via Rare on " + platform.system()

        self.RPC.update(large_image="logo",
                        details=title,
                        large_text=title,
                        state=os,
                        start=start)

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

