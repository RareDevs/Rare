from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeView, QDialog, QVBoxLayout

from rare.utils.json_formatter import QJsonModel


class DebugView(QTreeView):
    def __init__(self, data, parent=None):
        super(DebugView, self).__init__(parent=parent)
        self.setColumnWidth(0, 300)
        self.setWordWrap(True)
        self.model = QJsonModel(self)
        self.setModel(self.model)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        try:
            self.model.load(data)
        except Exception as e:
            pass
        self.resizeColumnToContents(0)


class DebugDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent=parent)
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        view = DebugView(data, self)
        layout.addWidget(view)
