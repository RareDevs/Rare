from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QCheckBox,
)

from rare.models.game import RareGame
from rare.models.install import UninstallOptionsModel
from rare.utils.misc import icon
from rare.widgets.dialogs import ButtonDialog, dialog_title_game


class UninstallDialog(ButtonDialog):
    result_ready = pyqtSignal(UninstallOptionsModel)

    def __init__(self, rgame: RareGame, options: UninstallOptionsModel, parent=None):
        super(UninstallDialog, self).__init__(parent=parent)
        header = self.tr("Uninstall")
        self.setWindowTitle(dialog_title_game(header, rgame.app_title))

        title_label = QLabel(f"<h4>{dialog_title_game(header, rgame.app_title)}</h4>", self)

        self.keep_files = QCheckBox(self.tr("Keep files"))
        self.keep_files.setChecked(bool(options.keep_files))

        self.keep_config = QCheckBox(self.tr("Keep configuation"))
        self.keep_config.setChecked(bool(options.keep_config))

        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addWidget(self.keep_files)
        layout.addWidget(self.keep_config)

        self.setCentralLayout(layout)

        self.accept_button.setText(self.tr("Uninstall"))
        self.accept_button.setIcon(icon("ri.uninstall-line"))
        self.accept_button.setObjectName("UninstallButton")

        if rgame.sdl_name is not None:
            self.keep_config.setChecked(True)

        self.options: UninstallOptionsModel = options

    def done_handler(self) -> None:
        self.result_ready.emit(self.options)

    def accept_handler(self):
        self.options.values = (
            True,
            self.keep_files.isChecked(),
            self.keep_config.isChecked(),
        )

    def reject_handler(self):
        self.options.values = (None, None, None)
