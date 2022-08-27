from typing import Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QCheckBox,
    QHBoxLayout,
    QPushButton,
)

from legendary.models.game import Game
from rare.utils.misc import icon


class UninstallDialog(QDialog):
    def __init__(self, game: Game):
        super(UninstallDialog, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowTitle("Uninstall Game")
        layout = QVBoxLayout()
        self.info_text = QLabel(
            self.tr("Do you really want to uninstall <b>{}</b> ?").format(game.app_title)
        )
        layout.addWidget(self.info_text)
        self.keep_files = QCheckBox(self.tr("Keep game files?"))
        self.keep_config = QCheckBox(self.tr("Keep game configuation?"))
        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(6, 6, 0, 6)
        form_layout.addWidget(self.keep_files)
        form_layout.addWidget(self.keep_config)
        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton(
            icon("ei.remove-circle", color="red"), self.tr("Uninstall")
        )
        self.ok_button.clicked.connect(self.ok)

        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.cancel)

        button_layout.addWidget(self.ok_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.options: Tuple[bool, bool, bool] = (False, False, False)

    def get_options(self) -> Tuple[bool, bool, bool]:
        self.exec_()
        return self.options

    def ok(self):
        self.options = (True, self.keep_files.isChecked(), self.keep_config.isChecked())
        self.close()

    def cancel(self):
        self.options = (False, False, False)
        self.close()
