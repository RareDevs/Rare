from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QStyle, QPushButton, QLineEdit

from rare.utils.misc import qta_icon


class ButtonLineEdit(QLineEdit):
    buttonClicked = pyqtSignal()

    def __init__(self, icon_name, placeholder_text: str, parent=None):
        super(ButtonLineEdit, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)

        self.button = QPushButton(self)
        self.button.setObjectName(f"{type(self).__name__}Button")
        self.button.setIcon(qta_icon(icon_name))
        self.button.setCursor(Qt.ArrowCursor)
        self.button.clicked.connect(self.buttonClicked.emit)

        self.setPlaceholderText(placeholder_text)
        # frame_width = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        # button_size = self.button.sizeHint()
        #
        # self.setStyleSheet(
        #     f"QLineEdit#{self.objectName()} {{padding-right: {(button_size.width() + frame_width + 1)}px; }}"
        # )
        # self.setMinimumSize(
        #     max(self.minimumSizeHint().width(), button_size.width() + frame_width * 2 + 2),
        #     max(
        #         self.minimumSizeHint().height(),
        #         button_size.height() + frame_width * 2 + 2,
        #     ),
        # )

    def resizeEvent(self, event):
        frame_width = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        button_size = self.button.sizeHint()
        self.button.move(
            self.rect().right() - frame_width - button_size.width(),
            (self.rect().bottom() - button_size.height() + 1) // 2,
        )
        super(ButtonLineEdit, self).resizeEvent(event)
