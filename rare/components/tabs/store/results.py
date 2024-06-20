from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QSizePolicy,
    QLabel,
    QScrollArea,
)

from rare.widgets.flow_layout import FlowLayout
from .api.models.response import CatalogOfferModel
from .widgets.items import ResultsItemWidget


class ResultsWidget(QScrollArea):
    show_details = pyqtSignal(CatalogOfferModel)

    def __init__(self, store_api, parent=None):
        super(ResultsWidget, self).__init__(parent=parent)
        self.store_api = store_api

        self.results_container = QWidget(self)
        self.results_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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
            self.store_api.search_game(text, self.show_results)

    def show_results(self, results: dict):
        for w in self.results_container.findChildren(QLabel, options=Qt.FindChildOption.FindDirectChildrenOnly):
            self.results_layout.removeWidget(w)
            w.deleteLater()
        for w in self.results_container.findChildren(ResultsItemWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            self.results_layout.removeWidget(w)
            w.deleteLater()

        if not results:
            self.results_layout.addWidget(QLabel(self.tr("No results found")))
        else:
            for res in results:
                w = ResultsItemWidget(self.store_api.cached_manager, res, parent=self.results_container)
                w.show_details.connect(self.show_details.emit)
                self.results_layout.addWidget(w)
        self.results_layout.update()
        self.setEnabled(True)

