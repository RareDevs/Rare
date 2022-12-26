from logging import getLogger

from PyQt5.QtCore import QEvent, pyqtSignal

from rare.models.game import RareGame
from rare.shared.game_utils import GameUtils
from rare.shared.image_manager import ImageSize
from .game_widget import GameWidget
from .icon_widget import IconWidget

logger = getLogger("IconGameWidget")


class IconGameWidget(GameWidget):
    is_ready = False
    update_game = pyqtSignal()

    def __init__(self, rgame: RareGame, game_utils: GameUtils, parent=None):
        super(IconGameWidget, self).__init__(rgame, game_utils, parent)
        self.setObjectName(f"{rgame.app_name}")
        self.setFixedSize(ImageSize.Display)
        self.ui = IconWidget()
        self.ui.setupUi(self)

        self.game_utils.finished.connect(self.game_finished)

        self.ui.title_label.setText(f"<h4>{self.rgame.app_title}</h4>")
        self.ui.launch_btn.clicked.connect(self.game_launch)
        self.ui.launch_btn.setVisible(self.rgame.is_installed)
        self.ui.install_btn.clicked.connect(self.install)
        self.ui.install_btn.setVisible(not self.rgame.is_installed)

        if self.rgame.igame and self.rgame.needs_verification:
            self.ui.status_label.setText(self.texts["static"]["needs_verification"])

        self.game_utils.game_launched.connect(self.game_started)

        self.is_ready = True
        self.ui.launch_btn.setEnabled(self.rgame.can_launch)

    def enterEvent(self, a0: QEvent = None) -> None:
        if a0 is not None:
            a0.accept()
        self.ui.status_label.setText(self.enterEventText)
        self.ui.enterAnimation(self)

    def leaveEvent(self, a0: QEvent = None) -> None:
        if a0 is not None:
            a0.accept()
        self.ui.leaveAnimation(self)
        self.ui.status_label.setText(self.leaveEventText)

    def game_launch(self):
        if not self.game_running:
            if self.rgame.igame and self.rgame.needs_verification:
                return
            if self.rgame.has_update:
                self.launch(skip_version_check=True)
            else:
                self.launch()

    def sync_finished(self, app_name):
        if not app_name == self.rgame.app_name:
            return
        super().sync_finished(app_name)
        self.leaveEvent(None)

    def game_finished(self, app_name, error):
        if app_name != self.rgame.app_name:
            return
        self.game_running = False
        self.leaveEvent(None)

    def game_started(self, app_name):
        if app_name == self.rgame.app_name:
            self.game_running = True
            self.leaveEvent(None)
