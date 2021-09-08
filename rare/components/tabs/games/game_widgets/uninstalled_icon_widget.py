from logging import getLogger

from PyQt5.QtWidgets import QVBoxLayout, QLabel

from legendary.core import LegendaryCore
from legendary.models.game import Game
from rare.components.tabs.games.game_widgets.base_uninstalled_widget import BaseUninstalledWidget

logger = getLogger("Uninstalled")


class IconWidgetUninstalled(BaseUninstalledWidget):

    def __init__(self, game: Game, core: LegendaryCore, pixmap):
        super(IconWidgetUninstalled, self).__init__(game, core, pixmap)
        self.layout = QVBoxLayout()
        self.setObjectName("game_widget_icon")
        self.layout.addWidget(self.image)

        self.title_label = QLabel(f"<h3>{game.app_title}</h3>")
        self.title_label.setWordWrap(True)
        self.layout.addWidget(self.title_label)

        self.info_label = QLabel("")
        self.layout.addWidget(self.info_label)

        self.setLayout(self.layout)
        self.setFixedWidth(self.sizeHint().width())

    def mousePressEvent(self, e) -> None:
        # left button
        if e.button() == 1 and not self.installing:
            self.install()

        # right
        elif e.button() == 2:
            pass  # self.showMenu(e)

    def enterEvent(self, e):
        if not self.installing:
            self.info_label.setText(self.tr("Game Info"))
        else:
            self.info_label.setText(self.tr("Installation running"))

    def leaveEvent(self, e):
        if self.installing:
            self.info_label.setText("Installation...")
        else:
            self.info_label.setText("")
