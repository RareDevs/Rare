from logging import getLogger

from PyQt5.QtCore import QEvent, pyqtSignal, QSize, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from qtawesome import icon

from rare import shared
from rare.components.tabs.games.game_widgets.base_installed_widget import BaseInstalledWidget

logger = getLogger("GameWidgetInstalled")


class InstalledIconWidget(BaseInstalledWidget):
    update_game = pyqtSignal()

    def __init__(self, app_name, pixmap, game_utils):
        super(InstalledIconWidget, self).__init__(app_name, pixmap, game_utils)
        self.setObjectName("game_widget_icon")

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.layout = QVBoxLayout()
        self.core = shared.core

        if self.update_available:
            logger.info("Update available for game: " + self.game.app_name)

        self.layout.addWidget(self.image)

        self.game_utils.finished.connect(self.game_finished)
        self.game_utils.cloud_save_finished.connect(self.sync_finished)

        self.title_label = QLabel(f"<h4>{self.game.app_title}</h4>")
        self.title_label.setAutoFillBackground(False)
        self.title_label.setWordWrap(True)
        self.title_label.setFixedWidth(175)
        minilayout = QHBoxLayout()
        self.title_label.setObjectName("game_widget")
        minilayout.addWidget(self.title_label)

        # Info Button
        self.menu_btn = QPushButton()
        self.menu_btn.setIcon(icon("ei.info-circle"))
        # self.menu_btn.setObjectName("installed_menu_button")
        self.menu_btn.setIconSize(QSize(18, 18))
        self.menu_btn.enterEvent = lambda x: self.info_label.setText(self.tr("Information"))
        self.menu_btn.leaveEvent = lambda x: self.enterEvent(None)
        # remove Border

        self.menu_btn.setObjectName("menu_button")

        self.menu_btn.clicked.connect(lambda: self.show_info.emit(self.game.app_name))
        self.menu_btn.setFixedWidth(17)
        minilayout.addWidget(self.menu_btn)
        minilayout.addStretch(1)
        self.layout.addLayout(minilayout)

        self.info_label = QLabel("")
        self.leaveEvent(None)
        self.info_label.setAutoFillBackground(False)
        self.info_label.setObjectName("info_label")
        self.layout.addWidget(self.info_label)

        if not self.is_origin and self.igame.needs_verification:
            self.info_label.setText(self.texts["needs_verification"])

        self.setLayout(self.layout)
        self.setFixedWidth(self.sizeHint().width())

        self.game_utils.game_launched.connect(self.game_started)

    def enterEvent(self, a0: QEvent = None) -> None:
        if self.game_running:
            self.info_label.setText(self.texts["hover"]["running"])
        elif not self.is_origin and self.igame.needs_verification:
            self.info_label.setText(self.texts["needs_verification"])
        elif self.update_available:
            self.info_label.setText(self.texts["hover"]["update_available"])
        else:
            self.info_label.setText(self.texts["hover"]["launch" if not self.is_origin else "launch_origin"])

    def leaveEvent(self, a0: QEvent = None) -> None:
        if self.game_running:
            self.info_label.setText(self.texts["default"]["running"])
        elif self.syncing_cloud_saves:
            self.info_label.setText(self.texts["default"]["syncing"])
        elif self.update_available:
            self.info_label.setText(self.texts["default"]["update_available"])
        elif self.igame and self.igame.needs_verification:
            self.info_label.setText(self.texts["needs_verification"])
        else:
            self.info_label.setText("")

    def mousePressEvent(self, e: QMouseEvent):
        # left button
        if e.button() == 1 and not self.game_running:
            if not self.is_origin and self.igame.needs_verification:
                return
            if self.update_available:
                self.launch(skip_version_check=True)
            else:
                self.launch()

        # right
        elif e.button() == 2:
            pass  # self.showMenu(e)

    def sync_finished(self, app_name):
        if not app_name == self.game.app_name:
            return
        super().sync_finished(app_name)
        self.leaveEvent(None)

    def game_finished(self, app_name, error):
        if app_name != self.game.app_name:
            return
        self.game_running = False
        self.leaveEvent(None)

    def game_started(self, app_name):
        if app_name == self.game.app_name:
            self.game_running = True
            self.leaveEvent(None)
