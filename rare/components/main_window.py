import os
from logging import getLogger

from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication

from rare import data_dir, shared
from rare.components.tabs.tab_widget import TabWidget
from rare.utils.rpc import DiscordRPC

logger = getLogger("Window")


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.settings = QSettings()
        self.core = shared.core

        self.signals = shared.signals

        self.offline = shared.args.offline
        width, height = 1200, 800
        if self.settings.value("save_size", False):
            width, height = self.settings.value("window_size", (1200, 800), tuple)

        desktop = QApplication.desktop()
        self.setGeometry((desktop.width() - width) / 2, (desktop.height() - height) / 2, width, height)

        self.setWindowTitle("Rare - GUI for legendary")
        self.tab_widget = TabWidget(self)
        self.setCentralWidget(self.tab_widget)
        if not shared.args.offline:
            self.rpc = DiscordRPC()
            self.tab_widget.delete_presence.connect(self.rpc.set_discord_rpc)
        if shared.args.subparser == "launch":
            if shared.args.app_name in [i.app_name for i in self.tab_widget.games_tab.installed]:
                logger.info("Launching " + self.core.get_installed_game(shared.args.app_name).title)
                self.tab_widget.games_tab.widgets[shared.args.app_name][1].launch()
            else:
                logger.info(
                    f"Could not find {shared.args.app_name} in Games or it is not installed")

        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_finished)
        self.timer.start(1000)

    def timer_finished(self):
        file_path = os.path.join(data_dir, "lockfile")
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
