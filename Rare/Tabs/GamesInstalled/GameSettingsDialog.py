import os

from PyQt5.QtWidgets import *

from Rare.ext.SettingsForm import SettingsForm
from Rare.utils.constants import game_settings


class GameSettingsDialog(QDialog):
    action: str = ""

    def __init__(self, game, parent):
        super(GameSettingsDialog, self).__init__(parent=parent)
        self.game = game
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("<h1>Settings</h1>"))

        self.uninstall_button = QPushButton("Uninstall Game")

        self.settings = SettingsForm(self.game.app_name, game_settings, table=True)

        self.uninstall_button.clicked.connect(self.uninstall)
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)

        self.layout.addWidget(self.settings)

        if os.name != 'nt':
            self.use_proton = QPushButton("Use Proton")
            self.use_proton.clicked.connect(self.settings.use_proton_template)
            self.layout.addWidget(self.use_proton)
        self.layout.addWidget(self.uninstall_button)
        self.layout.addWidget(self.exit_button)

        self.setLayout(self.layout)

    def get_settings(self):
        self.exec_()
        return self.action

    def uninstall(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(f"Do you really want to delete {self.game.title}")
        msg.setWindowTitle("Uninstall Game")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        ret = msg.exec_()

        if ret == QMessageBox.Ok:
            self.action = "uninstall"
            self.close()
            return
        else:
            self.action = ""
            self.close()

    def exit_settings(self):
        self.close()
