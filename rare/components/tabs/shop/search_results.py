from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGroupBox, QPushButton, \
    QStackedWidget

from rare.utils.extra_widgets import ImageLabel, FlowLayout, WaitingSpinner


class SearchResults(QStackedWidget):
    show_info = pyqtSignal(dict)

    def __init__(self, api_core):
        super(SearchResults, self).__init__()
        self.search_result_widget = QWidget()
        self.api_core = api_core
        self.addWidget(self.search_result_widget)
        self.main_layout = QVBoxLayout()
        self.back_button = QPushButton(self.tr("Back"))
        self.main_layout.addWidget(self.back_button)
        self.main_layout.addWidget(self.back_button)
        self.result_area = QScrollArea()
        self.widget = QWidget()
        self.result_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.result_area)
        self.result_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.result_area.setWidget(self.widget)
        self.layout = FlowLayout()
        self.widget.setLayout(self.layout)

        self.search_result_widget.setLayout(self.main_layout)

        self.addWidget(WaitingSpinner())
        self.setCurrentIndex(1)

    def load_results(self, text: str):
        self.setCurrentIndex(1)
        if text != "":
            self.api_core.search_game(text, self.show_results)

    def show_results(self, results: dict):
        QVBoxLayout().addWidget(self.widget)
        self.widget = QWidget()
        self.layout = FlowLayout()
        if not results:
            self.layout.addWidget(QLabel(self.tr("No results found")))
        else:
            for res in results:
                w = _SearchResultItem(res)
                w.show_info.connect(self.show_info.emit)
                self.layout.addWidget(w)
        self.widget.setLayout(self.layout)
        self.result_area.setWidget(self.widget)
        self.setCurrentIndex(0)


class _SearchResultItem(QGroupBox):
    res: dict
    show_info = pyqtSignal(dict)

    def __init__(self, result: dict):
        super(_SearchResultItem, self).__init__()
        self.layout = QVBoxLayout()
        self.image = ImageLabel()
        for img in result["keyImages"]:
            if img["type"] == "DieselStoreFrontTall":
                width = 240
                self.image.update_image(img["url"], result["title"], (width, 360))
                break
        else:
            print("No image found")
        self.layout.addWidget(self.image)

        self.res = result
        self.title = QLabel(self.res["title"])
        title_font = QFont()
        title_font.setPixelSize(15)
        self.title.setFont(title_font)
        self.title.setWordWrap(True)
        self.layout.addWidget(self.title)
        price = result['price']['totalPrice']['fmtPrice']['originalPrice']
        discount_price = result['price']['totalPrice']['fmtPrice']['discountPrice']
        price_layout = QHBoxLayout()
        price_label = QLabel(price if price != "0" else self.tr("Free"))
        price_layout.addWidget(price_label)

        if price != discount_price:
            font = QFont()
            font.setStrikeOut(True)
            price_label.setFont(font)
            price_layout.addWidget(QLabel(discount_price))
        # self.discount_price = QLabel(f"{self.tr('Discount price: ')}{discount_price}")
        self.layout.addLayout(price_layout)

        self.setLayout(self.layout)

        self.setFixedWidth(260)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.button() == 1:
            self.show_info.emit(self.res)
