from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QListWidgetItem, QWidget

from rare.ui.components.dialogs.install.file_filters import Ui_InstallDialogFileFilters
from rare.widgets.collapsible_widget import CollapsibleFrame


class InstallDialogFileFilters(CollapsibleFrame):
    def __init__(self, parent=None):
        super(InstallDialogFileFilters, self).__init__(parent=parent)

        title = self.tr("File filters")
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
        li.setFont(QFont("monospace"))
        li.setCheckState(Qt.CheckState.Unchecked)
        self.ui.exclude_list.addItem(li)


__all__ = ["InstallDialogFileFilters"]
