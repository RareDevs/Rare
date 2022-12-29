from logging import getLogger
from typing import List, Dict

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction

from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.models.game import RareGame

logger = getLogger("TrayIcon")


# FIXME: Remove when RareCore gets merged and replace it below
class RareGameMeta:
    def __init__(self):
        self.core = LegendaryCoreSingleton()
        metadata = RareGame.load_metadata_json()
        self.metadata: Dict[str, RareGame.Metadata] = {}
        for app_name, data in metadata.items():
            self.metadata[app_name] = RareGame.Metadata.from_dict(data)

    def get_list(self) -> List[str]:
        last_played = [
            item for item in self.metadata.items() if (bool(item[1]) and self.core.is_installed(item[0]))
        ]
        last_played.sort(key=lambda item: item[1].last_played, reverse=True)
        last_played = last_played[0:5]
        last_played = [item[0] for item in last_played]
        return last_played

class TrayIcon(QSystemTrayIcon):
    # none:
    show_app: pyqtSignal = pyqtSignal()
    # int: exit code
    exit_app: pyqtSignal = pyqtSignal(int)

    def __init__(self, parent=None):
        super(TrayIcon, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()

        self.setIcon(QIcon(":/images/Rare.png"))
        self.setVisible(True)
        self.setToolTip("Rare")

        self.menu = QMenu()

        self.show_action = QAction("Rare")
        self.show_action.triggered.connect(self.show_app)
        self.menu.addAction(self.show_action)

        self.menu.addSeparator()
        self.text_action = QAction("Quick launch")
        self.text_action.setEnabled(False)
        self.menu.addAction(self.text_action)

        metadata = RareGameMeta()
        last_played = metadata.get_list()

        self.game_actions: List[QAction] = []

        for app_name in last_played:
            a = QAction(self.core.get_game(app_name).app_title)
            a.setProperty("app_name", app_name)
            self.game_actions.append(a)
            a.triggered.connect(
                lambda: parent.tab_widget.games_tab.game_utils.prepare_launch(
                    self.sender().property("app_name"))
            )

        self.menu.addActions(self.game_actions)
        self.menu.addSeparator()

        self.exit_action = QAction(self.tr("Quit"))
        self.exit_action.triggered.connect(lambda: self.exit_app.emit(0))
        self.menu.addAction(self.exit_action)
        self.setContextMenu(self.menu)

        self.signals = GlobalSignalsSingleton()
        self.signals.game.uninstalled.connect(self.remove_button)

    def remove_button(self, app_name: str):
        if action := next((i for i in self.game_actions if i.property("app_name") == app_name), None):
            self.game_actions.remove(action)
            action.deleteLater()
