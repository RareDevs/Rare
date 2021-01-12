import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *


class CustomQLabel(QLabel):
    def __init__(self, *__args):
        super().__init__(*__args)
        self.app_name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)


class PathEdit(QWidget):
    def __init__(self, text: str = "", type_of_file: QFileDialog.FileType = QFileDialog.AnyFile, infotext: str = "",
                 filter: str = None):
        super(PathEdit, self).__init__()
        self.filter = filter
        self.type_of_file = type_of_file
        self.info_text = infotext
        self.layout = QHBoxLayout()
        self.text_edit = QLineEdit(text)
        self.path_select = QPushButton("Select Path")
        self.path_select.clicked.connect(self.set_path)
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.path_select)

        self.setLayout(self.layout)

    def setPlaceholderText(self, text: str):
        self.text_edit.setPlaceholderText(text)

    def text(self):
        return self.text_edit.text()

    def set_path(self):
        dlg = QFileDialog(self, "Choose Path", os.path.expanduser("~/"))
        dlg.setFileMode(self.type_of_file)
        if self.filter:
            dlg.setFilter(self.filter)
        if dlg.exec_():
            names = dlg.selectedFiles()
            self.text_edit.setText(names[0])
