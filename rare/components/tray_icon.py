from logging import getLogger
from typing import List

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QSettings
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication

from rare.shared import RareCore

logger = getLogger("TrayIcon")


class TrayIcon(QSystemTrayIcon):
    # none:
    show_app: pyqtSignal = pyqtSignal()
    # int: exit code
    exit_app: pyqtSignal = pyqtSignal(int)

    def __init__(self, parent=None):
        super(TrayIcon, self).__init__(parent=parent)
        self.__parent = parent
        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()
        self.settings = QSettings()

        self.setIcon(QIcon(":/images/Rare.png"))
        self.setVisible(True)
        self.setToolTip(QApplication.applicationName())

        self.menu = QMenu()

        self.show_action = QAction(QApplication.applicationName())
        self.show_action.triggered.connect(self.show_app)
        self.menu.addAction(self.show_action)

        self.menu.addSeparator()
        self.text_action = QAction("Quick launch")
        self.text_action.setEnabled(False)
        self.menu.addAction(self.text_action)

        # We need to reference this separator to add game actions before it
        self.separator = self.menu.addSeparator()
        self.exit_action = QAction(self.tr("Quit"))
        self.exit_action.triggered.connect(lambda: self.exit_app.emit(0))
        self.menu.addAction(self.exit_action)

        self.game_actions: List[QAction] = []
        self.update_actions()

        self.setContextMenu(self.menu)

        self.signals = RareCore.instance().signals()
        self.signals.game.uninstalled.connect(self.remove_button)
        self.signals.application.notify.connect(self.notify)
        self.signals.application.update_tray.connect(self.update_actions)

    def last_played(self) -> List:
        last_played = [game for game in self.rcore.games if (game.metadata and game.is_installed)]
        last_played.sort(key=lambda g: g.metadata.last_played, reverse=True)
        return last_played[0:5]

    @pyqtSlot(str)
    def notify(self, app_name: str):
        if self.settings.value("notification", True, bool):
            self.showMessage(
                self.tr("Download finished"),
                self.tr("Download finished. {} is playable now").format(
                    self.rcore.get_game(app_name).app_title
                ),
                self.Information,
                4000,
            )

    @pyqtSlot()
    def update_actions(self):
        for action in self.game_actions:
            action.deleteLater()
        self.game_actions.clear()
        for rgame in self.last_played():
            a = QAction(rgame.app_title)
            a.setProperty("app_name", rgame.app_name)
            a.triggered.connect(
                lambda: self.rcore.get_game(self.sender().property("app_name")).launch()
            )
            self.menu.insertAction(self.separator, a)
            self.game_actions.append(a)

    @pyqtSlot(str)
    def remove_button(self, app_name: str):
        if action := next((i for i in self.game_actions if i.property("app_name") == app_name), None):
            self.game_actions.remove(action)
            action.deleteLater()
