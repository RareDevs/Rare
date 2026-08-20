from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QLayout,
    QSizePolicy,
    QWidget,
)

from rare.widgets.loading_widget import LoadingWidget


class StoreGroup(QGroupBox):
    COLUMNS = 3

    def __init__(self, title: str, layout: type[QLayout] | None = None, parent=None):
        super().__init__(parent=parent)
        self.setTitle(title)
        self._count = 0

        self.grid_widget = QWidget(self)
        self.grid_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._grid = QGridLayout(self.grid_widget)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(12)
        self.main_layout = self._grid

        self.empty_label = QLabel()
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.empty_label.setVisible(False)

        self.loading_widget = LoadingWidget(True, parent=self)
        self.loading_widget.setFixedSize(QSize(48, 48))
        self.loading_widget.setVisible(False)

        root = QGridLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.grid_widget, 0, 0)
        root.addWidget(self.empty_label, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.loading_widget, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)

    def loading(self, state: bool) -> None:
        self.loading_widget.setVisible(state)
        if state:
            self.empty_label.setVisible(False)

    def add_widget(self, widget: QWidget) -> None:
        self.empty_label.setVisible(False)
        row = self._count // self.COLUMNS
        column = self._count % self.COLUMNS
        self._grid.addWidget(widget, row, column)
        self._count += 1

    def clear_widgets(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._count = 0

    def set_empty(self, text: str) -> None:
        self.empty_label.setText(text)
        self.empty_label.setVisible(True)
        self.loading_widget.setVisible(False)
