from logging import getLogger

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QStyle,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QLineEdit,
)

from rare.utils.misc import qta_icon

logger = getLogger("ExtraWidgets")


class SelectViewWidget(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, icon_view: bool, parent=None):
        super(SelectViewWidget, self).__init__(parent=parent)
        self.icon_button = QPushButton(self)
        self.icon_button.setObjectName(f"{type(self).__name__}Button")
        self.list_button = QPushButton(self)
        self.list_button.setObjectName(f"{type(self).__name__}Button")

        if icon_view:
            self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large", color="orange"))
            self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list", color="#eee"))
        else:
            self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large", color="#eee"))
            self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list", color="orange"))

        self.icon_button.clicked.connect(self.icon)
        self.list_button.clicked.connect(self.list)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.icon_button)
        layout.addWidget(self.list_button)

        self.setLayout(layout)

    def icon(self):
        self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large", color="orange"))
        self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list", color="#eee"))
        self.toggled.emit(True)

    def list(self):
        self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large", color="#eee"))
        self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list", color="orange"))
        self.toggled.emit(False)


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
