import os

from PyQt5.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QSpinBox, QFileDialog, QLabel, QPushButton, QHBoxLayout

from Rare.utils.QtExtensions import PathEdit


class InstallDialog(QDialog):
    infos = 0

    def __init__(self):
        super(InstallDialog, self).__init__()
        self.layout = QVBoxLayout()

        self.form = QFormLayout()
        default_path = os.path.expanduser("~/legendary")
        # TODO read from config
        self.install_path_field = PathEdit(text=default_path, type_of_file=QFileDialog.DirectoryOnly)
        self.form.addRow(QLabel("Install directory"), self.install_path_field)

        self.max_workes = QSpinBox()
        self.form.addRow(QLabel(self.tr("Max workers (0: Default)")), self.max_workes)

        self.layout.addLayout(self.form)

        self.ok_btn = QPushButton("Next")
        self.ok_btn.clicked.connect(self.ok)
        self.cancel = QPushButton("Cancel")
        self.cancel.clicked.connect(lambda: self.close())

        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.ok_btn)
        self.button_layout.addWidget(self.cancel)

        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def get_information(self):
        self.exec_()
        return self.infos

    def ok(self):
        self.infos = self.install_path_field.text(), self.max_workes.value()
        self.close()


class InstallInfoDialog(QDialog):
    accept: bool = False

    def __init__(self, dl_size, install_size):
        super(InstallInfoDialog, self).__init__()
        self.layout = QVBoxLayout()
        self.infos = QLabel(self.tr(
            "Download size: {}GB\nInstall size: {}GB").format(round(dl_size / 1024 ** 3, 2), round(install_size / 1024 ** 3, 2)))
        self.layout.addWidget(self.infos)

        self.btn_layout = QHBoxLayout()
        self.install_btn = QPushButton(self.tr("Install"))
        self.install_btn.clicked.connect(self.install)
        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.cancel)
        self.btn_layout.addStretch(1)
        self.btn_layout.addWidget(self.install_btn)
        self.btn_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.btn_layout)

        self.setLayout(self.layout)

    def get_accept(self):
        self.exec_()
        return self.accept

    def install(self):
        self.accept = True
        self.close()

    def cancel(self):
        self.accept = False
        self.close()
