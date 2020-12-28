import os

from PyQt5.QtWidgets import *

from Rare.Dialogs import AcceptDialog
from Rare.Tabs.GamesInstalled.SettingsForm import SettingsForm


class GameSettingsDialog(QDialog):
    action: str = ""

    def __init__(self, game, parent):
        super(GameSettingsDialog, self).__init__(parent=parent)
        self.game = game
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("<h1>Settings</h1>"))

        self.wine_prefix_text = QLabel("Wine prefix")
        self.wine_prefix = QLineEdit(f"{os.path.expanduser('~')}/.wine")
        self.wine_prefix.setPlaceholderText("Wineprefix")
        self.uninstall_button = QPushButton("Uninstall Game")

        self.settings = SettingsForm(self.game.app_name)

        self.uninstall_button.clicked.connect(self.uninstall)
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)

        self.layout.addWidget(self.settings)

        self.layout.addWidget(self.uninstall_button)
        self.layout.addWidget(self.exit_button)

        self.setLayout(self.layout)

    def get_settings(self):
        self.exec_()
        return self.action

    def uninstall(self):
        dia = AcceptDialog(f"Do you really want to delete {self.game.title}")
        if dia.get_accept():
            self.action = "uninstall"
            self.close()



    def exit_settings(self):
        self.close()
