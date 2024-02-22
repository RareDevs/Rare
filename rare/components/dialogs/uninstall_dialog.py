from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QCheckBox,
)

from rare.models.game import RareGame
from rare.models.install import UninstallOptionsModel
from rare.utils.misc import qta_icon
from rare.widgets.dialogs import ButtonDialog, game_title


class UninstallDialog(ButtonDialog):
    result_ready = pyqtSignal(UninstallOptionsModel)

    def __init__(self, rgame: RareGame, options: UninstallOptionsModel, parent=None):
        super(UninstallDialog, self).__init__(parent=parent)
        header = self.tr("Uninstall")
        self.setWindowTitle(game_title(header, rgame.app_title))
        self.setSubtitle(game_title(header, rgame.app_title))

        self.keep_files = QCheckBox(self.tr("Keep files"))
        self.keep_files.setChecked(bool(options.keep_files))
        self.keep_files.setEnabled(not rgame.is_overlay)

        self.keep_config = QCheckBox(self.tr("Keep configuation"))
        self.keep_config.setChecked(bool(options.keep_config))
        self.keep_config.setEnabled(not rgame.is_overlay)

        self.keep_overlay_keys = QCheckBox(self.tr("Keep EOS Overlay registry keys"))
        self.keep_overlay_keys.setChecked(bool(options.keep_overlay_keys))
        self.keep_overlay_keys.setEnabled(rgame.is_overlay)

        layout = QVBoxLayout()
        layout.addWidget(self.keep_files)
        layout.addWidget(self.keep_config)
        layout.addWidget(self.keep_overlay_keys)

        self.setCentralLayout(layout)

        self.accept_button.setText(self.tr("Uninstall"))
        self.accept_button.setIcon(qta_icon("ri.uninstall-line"))
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
            self.keep_overlay_keys.isChecked(),
        )

    def reject_handler(self):
        self.options.values = (None, None, None, None)
