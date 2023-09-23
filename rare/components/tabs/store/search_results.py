from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QWidget,
    QSizePolicy,
    QLabel, QScrollArea,
)

from rare.models.image import ImageSize
from rare.utils.qt_requests import QtRequestManager
from rare.widgets.flow_layout import FlowLayout
from rare.widgets.side_tab import SideTabContents
from .api.debug import DebugDialog
from .api.models.response import CatalogOfferModel
from .image_widget import ShopImageWidget


class SearchResultsWidget(QScrollArea):
    show_info = pyqtSignal(CatalogOfferModel)

    def __init__(self, api_core, parent=None):
        super(SearchResultsWidget, self).__init__(parent=parent)
        self.api_core = api_core

        self.results_container = QWidget(self)
        self.results_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.results_layout = FlowLayout(self.results_container)
        self.setWidget(self.results_container)
        self.setWidgetResizable(True)

        # self.main_layout = QVBoxLayout(self)
        # self.main_layout.setContentsMargins(0, 0, 0, 0)
        # self.main_layout.addWidget(self.results_scrollarea)

        self.setEnabled(False)

    def load_results(self, text: str):
        self.setEnabled(False)
        if text != "":
            self.api_core.search_game(text, self.show_results)

    def show_results(self, results: dict):
        for w in self.results_container.findChildren(QLabel, options=Qt.FindDirectChildrenOnly):
            self.results_layout.removeWidget(w)
            w.deleteLater()
        for w in self.results_container.findChildren(SearchResultItem, options=Qt.FindDirectChildrenOnly):
            self.results_layout.removeWidget(w)
            w.deleteLater()

        if not results:
            self.results_layout.addWidget(QLabel(self.tr("No results found")))
        else:
            for res in results:
                w = SearchResultItem(self.api_core.cached_manager, res, parent=self.results_container)
                w.show_info.connect(self.show_info.emit)
                self.results_layout.addWidget(w)
        self.results_layout.update()
        self.setEnabled(True)


class SearchResults(SearchResultsWidget, SideTabContents):
    def __init__(self, api_core, parent=None):
        super(SearchResults, self).__init__(api_core, parent=parent)
        self.implements_scrollarea = True


class SearchResultItem(ShopImageWidget):
    show_info = pyqtSignal(CatalogOfferModel)

    def __init__(self, manager: QtRequestManager, catalog_game: CatalogOfferModel, parent=None):
        super(SearchResultItem, self).__init__(manager, parent=parent)
        self.setFixedSize(ImageSize.Normal)
        self.ui.setupUi(self)

        key_images = catalog_game.key_images
        self.fetchPixmap(key_images.for_dimensions(self.width(), self.height()).url)

        self.ui.title_label.setText(catalog_game.title)

        price = catalog_game.price.total_price["fmtPrice"]["originalPrice"]
        discount_price = catalog_game.price.total_price["fmtPrice"]["discountPrice"]
        self.ui.price_label.setText(f'{price if price != "0" else self.tr("Free")}')
        if price != discount_price:
            font = self.ui.price_label.font()
            font.setStrikeOut(True)
            self.ui.price_label.setFont(font)
            self.ui.discount_label.setText(f'{discount_price if discount_price != "0" else self.tr("Free")}')
        else:
            self.ui.discount_label.setVisible(False)

        self.catalog_game = catalog_game

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            a0.accept()
            self.show_info.emit(self.catalog_game)
        if a0.button() == Qt.RightButton:
            a0.accept()
            dialog = DebugDialog(self.catalog_game.__dict__, self)
            dialog.show()

