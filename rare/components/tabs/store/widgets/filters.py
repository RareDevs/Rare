from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QGroupBox,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from rare.components.tabs.store.api.models.query import SearchStoreQuery
from rare.components.tabs.store.constants import Constants


class _FilterCheckBox(QCheckBox):
    activated = Signal(str)
    deactivated = Signal(str)

    def __init__(self, text: str, tag: str):
        super().__init__(text)
        self.tag = tag
        self.toggled.connect(self._handle)

    def _handle(self, checked: bool):
        if checked:
            self.activated.emit(self.tag)
        else:
            self.deactivated.emit(self.tag)


class FiltersWidget(QWidget):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self.price = ''
        self.tags: list[str] = []
        self.on_sale = False

        self._all_price_rb: QRadioButton | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self._build_body(layout)

    def _build_body(self, layout: QVBoxLayout):
        price_group = QGroupBox(self.tr('Price'))
        price_layout = QVBoxLayout(price_group)
        self._price_group = QButtonGroup(self)
        self._price_group.setExclusive(True)
        for text, value in [
            (self.tr('All'), ''),
            (self.tr('Free'), 'free'),
            (self.tr('Under 10'), '<price>[0, 1000)'),
            (self.tr('Under 20'), '<price>[0, 2000)'),
            (self.tr('Under 30'), '<price>[0, 3000)'),
            (self.tr('Above 15'), '<price>[1499,]'),
        ]:
            rb = QRadioButton(text)
            rb.setProperty('price', value)
            if value == '':
                rb.setChecked(True)
                self._all_price_rb = rb
            rb.toggled.connect(lambda checked, v=value: self._on_price(checked, v))
            self._price_group.addButton(rb)
            price_layout.addWidget(rb)
        layout.addWidget(price_group)

        self.on_sale_cb = QCheckBox(self.tr('On sale'))
        self.on_sale_cb.toggled.connect(self._on_sale)
        layout.addWidget(self.on_sale_cb)

        constants = Constants()
        for title, items in [
            (self.tr('Genre'), constants.categories),
            (self.tr('Platform'), constants.platforms),
            (self.tr('Other'), constants.others),
            (self.tr('Type'), constants.types),
        ]:
            group = QGroupBox(title)
            group_layout = QVBoxLayout(group)
            for text, tag in items:
                cb = _FilterCheckBox(text, tag)
                cb.activated.connect(self._on_tag_added)
                cb.deactivated.connect(self._on_tag_removed)
                group_layout.addWidget(cb)
            layout.addWidget(group)

    def _on_price(self, checked: bool, value: str):
        if checked:
            self.price = value
            self.changed.emit()

    def _on_sale(self, checked: bool):
        self.on_sale = checked
        self.changed.emit()

    def _on_tag_added(self, tag: str):
        if tag not in self.tags:
            self.tags.append(tag)
        self.changed.emit()

    def _on_tag_removed(self, tag: str):
        if tag in self.tags:
            self.tags.remove(tag)
        self.changed.emit()

    def reset(self):
        self.price = ''
        self.tags = []
        self.on_sale = False
        if self._all_price_rb is not None:
            self._all_price_rb.setChecked(True)
        self.on_sale_cb.setChecked(False)
        for cb in self.findChildren(_FilterCheckBox):
            cb.setChecked(False)
        self.changed.emit()

    def is_active(self) -> bool:
        return bool(self.price) or self.on_sale or bool(self.tags)

    def configure(self, query: SearchStoreQuery):
        query.price_range = self.price
        query.on_sale = self.on_sale
        query.tag = '|'.join(self.tags) if self.tags else ''
