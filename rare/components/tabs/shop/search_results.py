from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGroupBox


class SearchResults(QScrollArea):
    show_info = pyqtSignal(dict)

    # TODO nice look
    def __init__(self):
        super(SearchResults, self).__init__()
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)

    def show_results(self, results: list):
        QVBoxLayout().addWidget(self.widget)
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        for i in range(self.layout.count()):
            self.layout.removeItem(i)
        for res in results:
            w = _SearchResultItem(res)
            w.show_info.connect(self.show_info.emit)
            self.layout.addWidget(w)
        self.layout.addStretch(1)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)


class _SearchResultItem(QGroupBox):
    res: dict
    show_info = pyqtSignal(dict)

    def __init__(self, result: dict):
        super(_SearchResultItem, self).__init__()
        self.layout = QHBoxLayout()

        self.res = result
        self.title = QLabel(self.res["title"])
        self.layout.addWidget(self.title)
        original_price = result['price']['totalPrice']['fmtPrice']['originalPrice']
        self.price = QLabel(f"{self.tr('Original price: ')}{original_price}")
        self.layout.addWidget(self.price)

        self.setLayout(self.layout)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.button() == 1:
            self.show_info.emit(self.res)
