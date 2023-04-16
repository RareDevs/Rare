from logging import getLogger
from typing import Optional

from PyQt5.QtCore import QEvent

from rare.models.game import RareGame
from rare.models.image import ImageSize
from .game_widget import GameWidget
from .icon_widget import IconWidget

logger = getLogger("IconGameWidget")


class IconGameWidget(GameWidget):
    def __init__(self, rgame: RareGame, parent=None):
        super().__init__(rgame, parent)
        self.setObjectName(f"{rgame.app_name}")
        self.setFixedSize(ImageSize.Display)
        self.ui = IconWidget()
        self.ui.setupUi(self)

        self.ui.title_label.setText(self.rgame.app_title)
        self.ui.launch_btn.clicked.connect(self._launch)
        self.ui.launch_btn.setVisible(self.rgame.is_installed)
        self.ui.install_btn.clicked.connect(self._install)
        self.ui.install_btn.setVisible(not self.rgame.is_installed)

        self.ui.launch_btn.setEnabled(self.rgame.can_launch)

        self.update_state()

        # lk: "connect" the buttons' enter/leave events to this widget
        self.installEventFilter(self)
        self.ui.launch_btn.installEventFilter(self)
        self.ui.install_btn.installEventFilter(self)

    def enterEvent(self, a0: Optional[QEvent] = None) -> None:
        if a0 is not None:
            a0.accept()
        self.ui.enterAnimation(self)

    def leaveEvent(self, a0: Optional[QEvent] = None) -> None:
        if a0 is not None:
            a0.accept()
        self.ui.leaveAnimation(self)
