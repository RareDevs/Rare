import os
from logging import getLogger

from PyQt5.QtCore import Qt, QSettings, QTimer, QSize
from PyQt5.QtGui import QCloseEvent, QCursor
from PyQt5.QtWidgets import QMainWindow, QApplication, QStatusBar

from rare import data_dir, shared
from rare.components.tabs import TabWidget
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

        self.setWindowTitle("Rare - GUI for legendary")
        self.tab_widget = TabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        width, height = 1280, 720
        if self.settings.value("save_size", False, bool):
            width, height = self.settings.value("window_size", (width, height), tuple)

        # move the window outside the viewport
        self.move(-50000, -50000)
        # show the window in order for it to get decorated, otherwise windowHandle() is null
        self.show()
        # get the margins of the decorated window
        margins = self.windowHandle().frameMargins()
        # hide the window again because we don't want to show it at this point
        self.hide()
        # get the screen the cursor is on
        current_screen = QApplication.screenAt(QCursor.pos())
        # get the available screen geometry (excludes panels/docks)
        screen_rect = current_screen.availableGeometry()
        decor_width = margins.left() + margins.right()
        decor_height = margins.top() + margins.bottom()
        window_size = QSize(width, height).boundedTo(screen_rect.size() - QSize(decor_width, decor_height))
        self.resize(window_size)
        self.move(screen_rect.center() - self.rect().adjusted(0, 0, decor_width, decor_height).center())

        if not shared.args.offline:
            self.rpc = DiscordRPC()

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
                if game in [i.app_name for i in self.tab_widget.games_tab.game_list] and self.core.is_installed(game):
                    self.tab_widget.games_tab.game_utils.prepare_launch(game, offline=shared.args.offline)
                else:
                    logger.info(f"Could not find {game} in Games")
            elif action.startswith("start"):
                self.show()
            os.remove(file_path)
        self.timer.start(1000)

    def closeEvent(self, e: QCloseEvent):
        if self.settings.value("save_size", False, bool):
            size = self.size().width(), self.size().height()
            self.settings.setValue("window_size", size)
        if self.settings.value("sys_tray", True, bool):
            self.hide()
            e.ignore()
            return
        elif self.offline:
            pass
        e.accept()
