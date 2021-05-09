from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QLabel

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import Game
from rare.components.tabs.games.game_widgets.base_uninstalled_widget import BaseUninstalledWidget
from rare.utils.extra_widgets import ClickableLabel
from rare.utils.models import InstallOptions

logger = getLogger("Uninstalled")


class IconWidgetUninstalled(BaseUninstalledWidget):
    install_game = pyqtSignal(InstallOptions)

    def __init__(self, game: Game, core: LegendaryCore, pixmap):
        super(IconWidgetUninstalled, self).__init__(game, core, pixmap)
        self.layout = QVBoxLayout()
        self.setObjectName("game_widget_icon")
        if self.pixmap:
            w = 200
            self.pixmap = self.pixmap.scaled(w, int(w * 4 / 3))
            self.image = ClickableLabel()
            self.image.setPixmap(self.pixmap)
            self.layout.addWidget(self.image)

        self.title_label = QLabel(f"<h3>{game.app_title}</h3>")
        self.title_label.setWordWrap(True)
        self.layout.addWidget(self.title_label)

        self.info_label = QLabel("")
        self.layout.addWidget(self.info_label)

        self.setLayout(self.layout)
        self.setFixedWidth(self.sizeHint().width())

    def mousePressEvent(self, e) -> None:
        if not self.installing:
            self.install()

    def enterEvent(self, e):
        if not self.installing:
            self.info_label.setText(self.tr("Install Game"))
        else:
            self.info_label.setText(self.tr("Installation running"))

    def leaveEvent(self, e):
        if self.installing:
            self.info_label.setText("Installation...")
        else:
            self.info_label.setText("")
