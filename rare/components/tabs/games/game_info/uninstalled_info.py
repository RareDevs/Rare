from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import Game


class UninstalledInfo(QWidget):
    game: Game
    install_game = pyqtSignal(str)

    def __init__(self, core: LegendaryCore):
        super(UninstalledInfo, self).__init__()
        self.layout = QVBoxLayout()
        self.core = core

        self.top_layout = QHBoxLayout()

        self.image = QLabel()
        self.top_layout.addWidget(self.image)

        self.right_layout = QVBoxLayout()

        self.back = QPushButton(self.tr("Back"))
        self.right_layout.addWidget(self.back)

        self.title = QLabel("Error")
        self.right_layout.addWidget(self.title)

        self.app_name = QLabel("Error")
        self.right_layout.addWidget(self.app_name)

        self.rating = QLabel("Rating: Error")
        self.right_layout.addWidget(self.rating)

        self.install_button = QPushButton(self.tr("Install"))
        self.right_layout.addWidget(self.install_button)

        self.top_layout.addLayout(self.right_layout)

        self.layout.addLayout(self.top_layout)

        self.setLayout(self.layout)

    def update_game(self, app_name):
        self.game = self.core.get_game(app_name)

        self.title.setText(f"<h2>{self.game.app_title}</h2>")
        self.app_name.setText(app_name)

        # TODO get grade (Pull request)