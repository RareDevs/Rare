from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel
from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame, Game


class GameInfo(QWidget):
    igame: InstalledGame
    game: Game

    def __init__(self, core: LegendaryCore):
        super(GameInfo, self).__init__()
        self.core = core
        self.app_name = ""
        self.layout = QVBoxLayout()
        self.back_button = QPushButton("Back")
        self.layout.addWidget(self.back_button)

        # TODO More Information: Image text settings needs_verification platform

        self.game_title = QLabel("Error")
        self.layout.addWidget(self.game_title)

        self.setLayout(self.layout)

    def update_game(self, app_name):
        self.game = self.core.get_game(app_name)
        self.igame = self.core.get_installed_game(app_name)

        self.game_title.setText(self.game.app_title)
