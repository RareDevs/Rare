import os
from logging import getLogger

from PyQt5.QtCore import QSettings, QTimer
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from custom_legendary.core import LegendaryCore
from rare.components.tab_widget import TabWidget
from rare.utils.rpc import DiscordRPC

logger = getLogger("Window")


class MainWindow(QMainWindow):

    def __init__(self, core: LegendaryCore, args):
        super(MainWindow, self).__init__()
        self.settings = QSettings()
        self.core = core
        self.offline = args.offline
        width, height = 1200, 800
        if self.settings.value("save_size", False):
            width, height = self.settings.value("window_size", (1200, 800), tuple)

        self.setGeometry(0, 0, width, height)
        self.setWindowTitle("Rare - GUI for legendary")
        self.tab_widget = TabWidget(core, self, args.offline)
        self.setCentralWidget(self.tab_widget)
        if not args.offline:
            self.rpc = DiscordRPC(core)
            # Discord RPC on game launch
            self.tab_widget.games_tab.default_widget.game_list.game_started.connect(
                lambda: self.rpc.set_discord_rpc(self.tab_widget.games_tab.default_widget.game_list.running_games[0]))
            # Remove RPC
            self.tab_widget.delete_presence.connect(self.rpc.set_discord_rpc)
            # Show RPC on changed rare_settings
            self.tab_widget.settings.rare_settings.rpc.update_settings.connect(
                lambda: self.rpc.changed_settings(self.tab_widget.games_tab.default_widget.game_list.running_games))

        game = self.tab_widget.games_tab.default_widget.game_list.active_game
        if game != ("", 0) and not args.offline:
            self.rpc.set_discord_rpc(game[0])  # Appname

        if args.subparser == "launch":
            logger.info("Launching " + self.core.get_installed_game(args.app_name).title)
            if args.app_name in self.tab_widget.games_tab.default_widget.game_list.widgets.keys():
                self.tab_widget.games_tab.default_widget.game_list.widgets[args.app_name][1].launch()
            else:
                logger.info(f"Could not find {args.app_name} in Games")

        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_finished)
        self.timer.start(1000)

    def timer_finished(self):
        file_path = os.path.expanduser("~/.cache/rare/lockfile")
        if os.path.exists(file_path):
            file = open(file_path, "r")
            action = file.read()
            file.close()
            if action.startswith("launch"):
                game = action.replace("launch ", "").replace("\n", "")
                if game in self.tab_widget.games_tab.default_widget.game_list.widgets.keys():
                    self.tab_widget.games_tab.default_widget.game_list.widgets[game][1].launch()
                else:
                    logger.info(f"Could not find {game} in Games")

            elif action.startswith("start"):
                self.show()
            os.remove(file_path)
        self.timer.start(1000)

    def closeEvent(self, e: QCloseEvent):
        if self.settings.value("sys_tray", True, bool):
            self.hide()
            e.ignore()
            return
        elif self.offline:
            pass
        elif self.tab_widget.downloadTab.active_game is not None:
            if not QMessageBox.question(self, "Close",
                                        self.tr("There is a download active. Do you really want to exit app?"),
                                        QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                e.ignore()
                return
        if self.settings.value("save_size", False, bool):
            size = self.size().width(), self.size().height()
            self.settings.setValue("window_size", size)
        e.accept()
