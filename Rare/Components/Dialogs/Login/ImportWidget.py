from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from legendary.core import LegendaryCore


class ImportWidget(QWidget):
    success = pyqtSignal(str)

    def __init__(self, core: LegendaryCore):
        super(ImportWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.core = core

        self.back = QPushButton("Back")
        self.layout.addWidget(self.back)