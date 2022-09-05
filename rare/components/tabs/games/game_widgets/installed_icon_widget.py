from logging import getLogger

from PyQt5.QtCore import QEvent, pyqtSignal, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QWidget

from rare.components.tabs.games.game_widgets.base_installed_widget import (
    BaseInstalledWidget,
)
from rare.shared import LegendaryCoreSingleton
from rare.shared.image_manager import ImageSize
from rare.utils.misc import icon
from rare.widgets.elide_label import ElideLabel

logger = getLogger("GameWidgetInstalled")


class InstalledIconWidget(BaseInstalledWidget):
    update_game = pyqtSignal()

    def __init__(self, app_name, pixmap, game_utils):
        super(InstalledIconWidget, self).__init__(app_name, pixmap, game_utils)
        self.setObjectName(type(self).__name__)

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setFixedWidth(ImageSize.Display.size.width())
        self.core = LegendaryCoreSingleton()

        if self.update_available:
            logger.info(f"Update available for game: {self.game.app_name}")

        layout.addWidget(self.image)

        self.game_utils.finished.connect(self.game_finished)
        self.game_utils.cloud_save_finished.connect(self.sync_finished)

        miniwidget = QWidget(self)
        miniwidget.setFixedWidth(ImageSize.Display.size.width())
        minilayout = QHBoxLayout()
        minilayout.setContentsMargins(0, 0, 0, 0)
        minilayout.setSpacing(0)
        miniwidget.setLayout(minilayout)

        self.title_label = ElideLabel(f"<b>{self.game.app_title}</b>", parent=miniwidget)
        self.title_label.setAlignment(Qt.AlignTop)
        self.title_label.setObjectName("game_widget")
        minilayout.addWidget(self.title_label, stretch=2)

        # Info Button
        self.menu_btn = QPushButton(parent=miniwidget)
        self.menu_btn.setIcon(icon("ei.info-circle"))
        # self.menu_btn.setObjectName("installed_menu_button")
        self.menu_btn.enterEvent = lambda x: self.info_label.setText(self.tr("Information"))
        self.menu_btn.leaveEvent = lambda x: self.enterEvent(None)
        # remove Border

        self.menu_btn.setObjectName("menu_button")

        self.menu_btn.clicked.connect(lambda: self.show_info.emit(self.game.app_name))
        self.menu_btn.setFixedSize(22, 22)
        minilayout.addWidget(self.menu_btn, stretch=0)
        minilayout.setAlignment(Qt.AlignTop)
        layout.addWidget(miniwidget)

        self.info_label = ElideLabel(" ", parent=self)
        self.info_label.setFixedWidth(ImageSize.Display.size.width())
        self.leaveEvent(None)
        self.info_label.setObjectName("info_label")
        layout.addWidget(self.info_label)

        if self.igame and self.igame.needs_verification:
            self.info_label.setText(self.texts["needs_verification"])

        self.setLayout(layout)

        self.game_utils.game_launched.connect(self.game_started)

    def enterEvent(self, a0: QEvent = None) -> None:
        if self.game_running:
            self.info_label.setText(self.texts["hover"]["running"])
        elif self.igame and self.igame.needs_verification:
            self.info_label.setText(self.texts["needs_verification"])
        elif self.is_only_offline:
            self.info_label.setText(self.texts["hover"]["launch_offline"])
        elif self.update_available:
            self.info_label.setText(self.texts["hover"]["update_available"])
        else:
            self.info_label.setText(
                self.texts["hover"]["launch" if self.igame else "launch_origin" if self.is_origin else "no_launch"]
            )

    def leaveEvent(self, a0: QEvent = None) -> None:
        if self.game_running:
            self.info_label.setText(self.texts["default"]["running"])
        elif self.syncing_cloud_saves:
            self.info_label.setText(self.texts["default"]["syncing"])
        elif self.is_only_offline:
            self.info_label.setText(self.texts["default"]["no_meta"])
        elif self.update_available:
            self.info_label.setText(self.texts["default"]["update_available"])
        elif self.igame and self.igame.needs_verification:
            self.info_label.setText(self.texts["needs_verification"])
        else:
            self.info_label.setText(" ")  # invisible text, cheap way to always vertical have size in label

    def mousePressEvent(self, e: QMouseEvent):
        # left button
        if e.button() == 1 and not self.game_running:
            if self.igame and self.igame.needs_verification:
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
