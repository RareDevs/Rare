from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
    QWidget,
)

from rare.shared import RareCore
from .api.models.response import CatalogOfferModel
from .widgets.items import SearchItemWidget, StoreItemWidget


class ResultsWidget(QScrollArea):
    COLUMNS = 3
    show_details = Signal(CatalogOfferModel)

    def __init__(self, store_api, rcore: RareCore | None = None, parent=None):
        super(ResultsWidget, self).__init__(parent=parent)
        self.store_api = store_api
        self.rcore = rcore
        self._index = 0

        self.results_container = QWidget(self)
        self.results_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.results_layout = QGridLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(12)
        self.setWidget(self.results_container)
        self.setWidgetResizable(True)

        self.setEnabled(False)

    def _clear(self):
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._index = 0

    def _add(self, widget: QWidget):
        self.results_layout.addWidget(widget, self._index // self.COLUMNS, self._index % self.COLUMNS)
        self._index += 1

    def load_results(self, text: str):
        self.setEnabled(False)
        if text != '':
            self.store_api.search_game(text, self.show_results)

    def show_results(self, results: dict):
        self._clear()
        if not results:
            self.results_layout.addWidget(QLabel(self.tr('No results found')), 0, 0)
        else:
            for res in results:
                w = SearchItemWidget(self.store_api.image_manager, res, self.rcore, parent=self.results_container)
                w.show_details.connect(self.show_details)
                self._add(w)
        self.setEnabled(True)

    def show_browse(self, results: list):
        self._clear()
        if not results:
            self.results_layout.addWidget(QLabel(self.tr('No results found')), 0, 0)
        else:
            for game in results:
                w = StoreItemWidget(self.store_api.image_manager, game, self.rcore, parent=self.results_container)
                w.show_details.connect(self.show_details)
                self._add(w)
        self.setEnabled(True)
