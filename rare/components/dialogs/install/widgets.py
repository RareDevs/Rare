from PySide6.QtGui import QFont, Qt
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QListWidgetItem, QWidget

from rare.ui.components.dialogs.install.file_filters import Ui_InstallDialogFileFilters
from rare.widgets.collapsible_widget import CollapsibleFrame


class InstallDialogEulaWidget(QWidget):
    def __init__(self, *, parent: QWidget | None = None):
        super(InstallDialogEulaWidget, self).__init__(parent=parent)

        font = self.font()
        font.setItalic(True)

        self.check = QCheckBox(self.tr('EULAs:'), parent=self)
        self.check.setObjectName('InfoLabel')
        self.check.setFont(font)
        self.label = QLabel(self.tr('All EULAs have been accepted'))
        self.label.setObjectName('InfoLabel')
        self.label.setFont(font)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.check, stretch=0)
        layout.addWidget(self.label, stretch=1)

        self.pending_eulas: list = []

    def setup_widget(self, pending_eulas: list):
        self.check.setEnabled(bool(pending_eulas))
        self.check.setCheckState(Qt.CheckState.Unchecked if pending_eulas else Qt.CheckState.Checked)
        self.label.setEnabled(bool(pending_eulas))
        label_text: list = []
        for eula in pending_eulas:
            label_text.append(f'<a href=\"{eula.get("url")}\">{eula.get("key")}</a>')
        if label_text:
            self.label.setText(', '.join(label_text))
        self.pending_eulas = pending_eulas


class InstallDialogFileFilters(CollapsibleFrame):
    def __init__(self, parent=None):
        super(InstallDialogFileFilters, self).__init__(parent=parent)

        title = self.tr('File filters')
        self.setTitle(title)

        self.widget = QWidget(parent=self)
        self.ui = Ui_InstallDialogFileFilters()
        self.ui.setupUi(self.widget)
        self.setWidget(self.widget)

        # self.ui.exclude_prefix_label.setVisible(False)
        # self.ui.exclude_prefix_info.setVisible(False)
        # self.ui.exclude_prefix_button.setVisible(False)

    def clear(self):
        self.ui.exclude_list.clear()

    def add_item(self, data: str):
        li = QListWidgetItem(data, self.ui.exclude_list)
        li.setFont(QFont('monospace'))
        li.setCheckState(Qt.CheckState.Unchecked)
        self.ui.exclude_list.addItem(li)


__all__ = ['InstallDialogEulaWidget', 'InstallDialogFileFilters']
