from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QPushButton

from legendary.core import LegendaryCore
from rare.components.tabs.games.game_widgets.base_uninstalled_widget import (
    BaseUninstalledWidget,
)

logger = getLogger("Game")


class UninstalledListWidget(BaseUninstalledWidget):
    def __init__(self, core: LegendaryCore, game, pixmap):
        super(UninstalledListWidget, self).__init__(game, core, pixmap)
        self.setFrameStyle(self.StyledPanel)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.image)

        self.child_layout = QVBoxLayout()
        layout.addLayout(self.child_layout)

        self.title_label = QLabel(f"<h2>{self.game.app_title}</h2>")
        self.app_name_label = QLabel(f"App Name: {self.game.app_name}")
        self.install_button = QPushButton(self.tr("Install"))
        self.install_button.setFixedWidth(120)
        self.install_button.clicked.connect(self.install)

        self.child_layout.addWidget(self.title_label)
        self.child_layout.addWidget(self.app_name_label)
        self.child_layout.addWidget(self.install_button)

        layout.setAlignment(Qt.AlignLeft)
        self.child_layout.setAlignment(Qt.AlignTop)
