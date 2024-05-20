from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QWidget,
    QPushButton,
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


