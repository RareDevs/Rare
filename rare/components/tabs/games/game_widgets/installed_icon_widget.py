from logging import getLogger

from PyQt5.QtCore import QEvent, pyqtSignal, QSize, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import *
from qtawesome import icon

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import InstalledGame
from rare.components.tabs.games.game_widgets.base_installed_widget import BaseInstalledWidget
from rare.utils.extra_widgets import ClickableLabel

logger = getLogger("GameWidgetInstalled")


class GameWidgetInstalled(BaseInstalledWidget):
    update_list = pyqtSignal()
    show_info = pyqtSignal(str)
    update_game = pyqtSignal()

    def __init__(self, game: InstalledGame, core: LegendaryCore, pixmap, offline):
        super(GameWidgetInstalled, self).__init__(game, core, pixmap, offline)
        self.setObjectName("game_widget_icon")

        self.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.layout = QVBoxLayout()
        self.core = core
        self.running = False
        self.info_text = ""

        if self.update_available:
            logger.info("Update available for game: " + self.game.app_name)
            self.info_text = self.tr("Update available")

        if self.pixmap:
            w = 200
            self.pixmap = self.pixmap.scaled(w, int(w * 4 / 3), transformMode=Qt.SmoothTransformation)
            self.image = ClickableLabel()
            self.image.setObjectName("game_widget")
            self.image.setPixmap(self.pixmap)
            self.layout.addWidget(self.image)

        self.title_label = QLabel(f"<h4>{game.title}</h4>")
        self.title_label.setAutoFillBackground(False)
        self.title_label.setWordWrap(True)
        self.title_label.setFixedWidth(175)
        minilayout = QHBoxLayout()
        self.title_label.setObjectName("game_widget")
        minilayout.addWidget(self.title_label)

        # Info Button
        self.menu_btn = QPushButton()
        self.menu_btn.setIcon(icon("ei.info-circle", color="white"))
        # self.menu_btn.setObjectName("installed_menu_button")
        self.menu_btn.setIconSize(QSize(18, 18))
        self.menu_btn.enterEvent = lambda x: self.info_label.setText("Information")
        self.menu_btn.leaveEvent = lambda x: self.info_label.setText(
            "Please update Game") if self.update_available else self.info_label.setText("Start Game")
        # remove Border

        self.menu_btn.setObjectName("menu_button")

        self.menu_btn.clicked.connect(lambda: self.show_info.emit(self.game.app_name))
        self.menu_btn.setFixedWidth(17)
        minilayout.addWidget(self.menu_btn)
        minilayout.addStretch(1)
        self.layout.addLayout(minilayout)

        self.info_label = QLabel(self.info_text)
        self.info_label.setAutoFillBackground(False)
        self.info_label.setObjectName("info_label")
        self.layout.addWidget(self.info_label)

        # p = self.palette()
        # p.setColor(self.backgroundRole(), Qt.red)
        # self.setPalette(p)

        self.setLayout(self.layout)
        self.setFixedWidth(self.sizeHint().width())

    def enterEvent(self, a0: QEvent) -> None:
        if self.game_running:
            self.info_label.setText(self.tr("Game running"))
        elif self.update_available:
            self.info_label.setText(self.tr("Start game without version check"))
        else:
            self.info_label.setText("Start Game")

    def leaveEvent(self, a0: QEvent) -> None:
        if self.running:
            self.info_label.setText(self.tr("Game running"))
        else:
            self.info_label.setText(self.info_text)

    def mousePressEvent(self, e: QMouseEvent):
        # left button
        if e.button() == 1 and not self.game_running:
            if self.update_available:
                self.launch(skip_version_check=True)
            else:
                self.launch()

        # right
        elif e.button() == 2:
            pass  # self.showMenu(e)

    """def showMenu(self, event):
        menu = QMenu()
        desktop_link = menu.addAction("Add Desktop link")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == desktop_link:
            print("LOL")"""
