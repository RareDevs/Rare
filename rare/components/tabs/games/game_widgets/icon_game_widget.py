from logging import getLogger
from typing import Optional

from PyQt5.QtCore import QEvent, pyqtSlot

from rare.models.game import RareGame
from rare.shared.image_manager import ImageSize
from .game_widget import GameWidget
from .icon_widget import IconWidget

logger = getLogger("IconGameWidget")


class IconGameWidget(GameWidget):
    def __init__(self, rgame: RareGame, parent=None):
        super(IconGameWidget, self).__init__(rgame, parent)
        self.setObjectName(f"{rgame.app_name}")
        self.setFixedSize(ImageSize.Display)
        self.ui = IconWidget()
        self.ui.setupUi(self)

        self.ui.title_label.setText(f"<h4>{self.rgame.app_title}</h4>")
        self.ui.launch_btn.clicked.connect(self._launch)
        self.ui.launch_btn.setVisible(self.rgame.is_installed)
        self.ui.install_btn.clicked.connect(self._install)
        self.ui.install_btn.setVisible(not self.rgame.is_installed)

        self.ui.launch_btn.setEnabled(self.rgame.can_launch)

        self.set_status()

    @pyqtSlot()
    def set_status(self):
        super(IconGameWidget, self).set_status(self.ui.status_label)

    @pyqtSlot()
    def update_widget(self):
        super(IconGameWidget, self).update_widget(self.ui.install_btn, self.ui.launch_btn)

    def enterEvent(self, a0: Optional[QEvent] = None) -> None:
        if a0 is not None:
            a0.accept()
        self.ui.tooltip_label.setText(self.enterEventText)
        self.ui.enterAnimation(self)

    def leaveEvent(self, a0: Optional[QEvent] = None) -> None:
        if a0 is not None:
            a0.accept()
        self.ui.leaveAnimation(self)
        self.ui.tooltip_label.setText(self.leaveEventText)

    # def sync_finished(self, app_name):
    #     if not app_name == self.rgame.app_name:
    #         return
    #     super().sync_finished(app_name)
    #     self.leaveEvent(None)

    # def game_finished(self, app_name, error):
    #     if app_name != self.rgame.app_name:
    #         return
    #     self.game_running = False
    #     self.leaveEvent(None)
    #
    # def game_started(self, app_name):
    #     if app_name == self.rgame.app_name:
    #         self.game_running = True
    #         self.leaveEvent(None)
