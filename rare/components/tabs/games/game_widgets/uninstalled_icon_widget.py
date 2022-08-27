from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout
from legendary.core import LegendaryCore
from legendary.models.game import Game

from rare.components.tabs.games.game_widgets.base_uninstalled_widget import (
    BaseUninstalledWidget,
)
from rare.shared.image_manager import ImageSize
from rare.widgets.elide_label import ElideLabel

logger = getLogger("Uninstalled")


class UninstalledIconWidget(BaseUninstalledWidget):
    def __init__(self, game: Game, core: LegendaryCore, pixmap):
        super(UninstalledIconWidget, self).__init__(game, core, pixmap)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setObjectName(type(self).__name__)
        layout.addWidget(self.image)

        miniwidget = QWidget(self)
        miniwidget.setFixedWidth(ImageSize.Display.size.width())
        minilayout = QHBoxLayout()
        minilayout.setContentsMargins(0, 0, 0, 0)
        minilayout.setSpacing(0)
        miniwidget.setLayout(minilayout)

        self.title_label = ElideLabel(f"<b>{game.app_title}</b>", parent=miniwidget)
        self.title_label.setAlignment(Qt.AlignTop)
        self.title_label.setObjectName("game_widget")
        minilayout.addWidget(self.title_label, stretch=2)

        minilayout.setAlignment(Qt.AlignTop)
        layout.addWidget(miniwidget)

        self.info_label = ElideLabel(" ", parent=self)
        self.info_label.setFixedWidth(ImageSize.Display.size.width())
        self.leaveEvent(None)
        self.info_label.setObjectName("info_label")
        layout.addWidget(self.info_label)

        self.setLayout(layout)

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
            self.info_label.setText(" ")  # invisible text, cheap way to always have vertical size in label
