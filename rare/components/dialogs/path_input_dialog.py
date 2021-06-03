from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QLabel, QDialog, QFileDialog

from rare.utils.extra_widgets import PathEdit


class PathInputDialog(QDialog):
    def __init__(self, title_text, text, path="Select Directory"):
        super().__init__()
        self.path = ""
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowTitle(title_text)
        self.info_label = QLabel(text)
        self.info_label.setWordWrap(True)

        self.input = PathEdit(path, QFileDialog.DirectoryOnly)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.info_label)
        self.layout.addWidget(self.input)

        self.child_layout = QHBoxLayout()
        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(self.ok)
        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.cancel)
        self.child_layout.addStretch()
        self.child_layout.addWidget(self.ok_button)
        self.child_layout.addWidget(self.cancel_button)

        self.layout.addLayout(self.child_layout)

        self.setLayout(self.layout)

    def get_path(self):
        self.exec_()
        return self.path

    def cancel(self):
        self.path = ""
        self.close()

    def ok(self):
        self.path = self.input.text()
        self.close()
