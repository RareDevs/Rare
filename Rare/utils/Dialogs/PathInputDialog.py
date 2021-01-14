from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QApplication

from Rare.ext.QtExtensions import CustomQLabel, PathEdit

class DLG(QDialog):
    def __init__(self):
        super(DLG, self).__init__()
        print("lol")

class PathInputDialog(QDialog):
    def __init__(self, title_text, text):
        super().__init__()
        self.path = ""

        self.setWindowTitle(title_text)
        self.info_label = CustomQLabel(text)
        self.info_label.setWordWrap(True)

        self.input = PathEdit(self.tr("Select directory"), QFileDialog.DirectoryOnly)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.info_label)
        self.layout.addWidget(self.input)

        self.child_layout = QHBoxLayout()
        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(self.ok)
        self.cancel_button = QPushButton("Cancel")
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
