from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
)

from rare.shared.image_manager import ImageSize
from rare.widgets.flow_layout import FlowLayout
from rare.widgets.elide_label import ElideLabel
from .image_widget import ShopImageWidget


class SearchResults(QWidget):
    show_info = pyqtSignal(dict)

    def __init__(self, api_core, parent=None):
        super(SearchResults, self).__init__(parent=parent)
        self.api_core = api_core

        self.results_frame = QFrame(self)
        self.results_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.results_frame.setFrameStyle(QFrame.StyledPanel)
        self.resutls_layout = FlowLayout(self.results_frame)
        self.results_frame.setLayout(self.resutls_layout)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.results_frame)

        self.setLayout(self.main_layout)
        self.setEnabled(False)

    def load_results(self, text: str):
        self.setEnabled(False)
        if text != "":
            self.api_core.search_game(text, self.show_results)

    def show_results(self, results: dict):
        for w in self.results_frame.findChildren(QLabel, options=Qt.FindDirectChildrenOnly):
            self.results_frame.layout().removeWidget(w)
            w.deleteLater()
        for w in self.results_frame.findChildren(_SearchResultItem, options=Qt.FindDirectChildrenOnly):
            self.results_frame.layout().removeWidget(w)
            w.deleteLater()

        if not results:
            self.results_frame.layout().addWidget(QLabel(self.tr("No results found")))
        else:
            for res in results:
                w = _SearchResultItem(res, parent=self.results_frame)
                w.show_info.connect(self.show_info.emit)
                self.results_frame.layout().addWidget(w)
        self.setEnabled(True)


class _SearchResultItem(QFrame):
    res: dict
    show_info = pyqtSignal(dict)

    def __init__(self, result: dict, parent=None):
        super(_SearchResultItem, self).__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.widget_layout = QVBoxLayout()
        self.widget_layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self.image = ShopImageWidget(parent=self)
        self.image.setFixedSize(ImageSize.Normal)
        for img in result["keyImages"]:
            if img["type"] in ["DieselStoreFrontTall", "OfferImageTall", "Thumbnail", "ProductLogo"]:
                self.image.fetchPixmap(img["url"], result["id"], result["title"])
                break
        else:
            print("No image found")
        self.widget_layout.addWidget(self.image)

        self.res = result
        self.title = ElideLabel(self.res["title"], parent=self)
        title_font = QFont()
        title_font.setPixelSize(15)
        self.title.setFont(title_font)
        self.title.setWordWrap(False)
        self.widget_layout.addWidget(self.title)
        price = result["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
        discount_price = result["price"]["totalPrice"]["fmtPrice"]["discountPrice"]
        price_layout = QHBoxLayout()
        price_layout.addStretch(1)
        price_label = QLabel(price if price != "0" else self.tr("Free"), parent=self)
        price_label.setAlignment(Qt.AlignRight)
        price_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        price_layout.addWidget(price_label)

        if price != discount_price:
            font = QFont()
            font.setStrikeOut(True)
            price_label.setFont(font)
            discount_label = QLabel(discount_price if discount_price != "0" else self.tr("Free"), parent=self)
            discount_label.setAlignment(Qt.AlignRight)
            discount_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            price_layout.addWidget(discount_label)
        # self.discount_price = QLabel(f"{self.tr('Discount price: ')}{discount_price}")
        self.widget_layout.addLayout(price_layout)

        self.setLayout(self.widget_layout)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.button() == 1:
            self.show_info.emit(self.res)
