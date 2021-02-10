import os

from PyQt5.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QSpinBox, QFileDialog, QLabel, QPushButton, QHBoxLayout

from Rare.utils.QtExtensions import PathEdit


class InstallDialog(QDialog):
    def __init__(self):
        super(InstallDialog, self).__init__()
        self.layout = QVBoxLayout()

        self.form = QFormLayout()
        default_path = os.path.expanduser("~/legendary")
        #TODO read from config
        self.install_path_field = PathEdit(text=default_path, type_of_file=QFileDialog.DirectoryOnly)
        self.form.addRow(QLabel("Install directory"), self.install_path_field)

        self.max_workes = QSpinBox()
        self.form.addRow(QLabel("Max workers"), self.max_workes)

        self.layout.addLayout(self.form)

        self.ok = QPushButton("Install")
        self.cancel = QPushButton("Cancel")

        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.ok)
        self.button_layout.addWidget(self.cancel)

        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def get_information(self):
        self.exec_()
        return self.install_path_field.text(), self.max_workes.value()
