from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QCheckBox, QFormLayout, QHBoxLayout, QPushButton
from qtawesome import icon

from legendary.models.game import Game


class UninstallDialog(QDialog):
    def __init__(self, game: Game):
        super(UninstallDialog, self).__init__()
        self.setWindowTitle("Uninstall Game")
        self.info = 0
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.layout = QVBoxLayout()
        self.info_text = QLabel(self.tr("Do you really want to uninstall {}").format(game.app_title))
        self.layout.addWidget(self.info_text)
        self.keep_files = QCheckBox(self.tr("Keep Files"))
        self.form = QFormLayout()
        self.form.setContentsMargins(0, 10, 0, 10)
        self.form.addRow(QLabel(self.tr("Do you want to keep files?")), self.keep_files)
        self.layout.addLayout(self.form)

        self.button_layout = QHBoxLayout()
        self.ok_button = QPushButton(icon("ei.remove-circle", color="red"), self.tr("Uninstall"))
        self.ok_button.clicked.connect(self.ok)

        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.cancel)

        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def get_information(self):
        self.exec_()
        return self.info

    def ok(self):
        self.info = {"keep_files": self.keep_files.isChecked()}
        self.close()

    def cancel(self):
        self.info = 0
        self.close()
