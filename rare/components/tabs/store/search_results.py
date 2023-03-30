from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QFrame,
    QWidget,
    QVBoxLayout,
    QSizePolicy,
    QLabel,
)

from rare.shared.image_manager import ImageSize
from rare.widgets.flow_layout import FlowLayout
from .image_widget import ShopImageWidget


class SearchResults(QWidget):
    show_info = pyqtSignal(dict)

    def __init__(self, api_core, parent=None):
        super(SearchResults, self).__init__(parent=parent)
        self.api_core = api_core

        self.results_frame = QFrame(self)
        self.results_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.results_frame.setFrameStyle(QFrame.StyledPanel)
        self.results_layout = FlowLayout(self.results_frame)
        self.results_frame.setLayout(self.results_layout)

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
            self.results_layout.removeWidget(w)
            w.deleteLater()
        for w in self.results_frame.findChildren(SearchResultItem, options=Qt.FindDirectChildrenOnly):
            self.results_layout.removeWidget(w)
            w.deleteLater()

        if not results:
            self.results_layout.addWidget(QLabel(self.tr("No results found")))
        else:
            for res in results:
                w = SearchResultItem(res, parent=self.results_frame)
                w.show_info.connect(self.show_info.emit)
                self.results_layout.addWidget(w)
        self.setEnabled(True)


class SearchResultItem(ShopImageWidget):
    show_info = pyqtSignal(dict)

    def __init__(self, result: dict, parent=None):
        super(SearchResultItem, self).__init__(parent=parent)
        self.setFixedSize(ImageSize.Normal)
        self.ui.setupUi(self)
        for img in result["keyImages"]:
            if img["type"] in ["DieselStoreFrontTall", "OfferImageTall", "Thumbnail", "ProductLogo"]:
                self.fetchPixmap(img["url"], result["id"], result["title"])
                break
        else:
            print("No image found")

        self.ui.title_label.setText(result["title"])
        price = result["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
        discount_price = result["price"]["totalPrice"]["fmtPrice"]["discountPrice"]
        self.ui.price_label.setText(f'{price if price != "0" else self.tr("Free")}')
        if price != discount_price:
            font = self.ui.price_label.font()
            font.setStrikeOut(True)
            self.ui.price_label.setFont(font)
            self.ui.discount_label.setText(f'{discount_price if discount_price != "0" else self.tr("Free")}')
        else:
            self.ui.discount_label.setVisible(False)

        self.res = result

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            a0.accept()
            self.show_info.emit(self.res)
