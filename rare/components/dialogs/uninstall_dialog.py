from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
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

        self.keep_folder = QCheckBox(self.tr("Keep game folder"))
        self.keep_folder.setChecked(bool(options.keep_folder))
        self.keep_folder.setEnabled(not rgame.is_overlay)

        self.keep_config = QCheckBox(self.tr("Keep configuation"))
        self.keep_config.setChecked(bool(options.keep_config))
        self.keep_config.setEnabled(not rgame.is_overlay)

        self.keep_overlay_keys = QCheckBox(self.tr("Keep EOS Overlay registry keys"))
        self.keep_overlay_keys.setChecked(bool(options.keep_overlay_keys))
        self.keep_overlay_keys.setEnabled(rgame.is_overlay)

        layout = QVBoxLayout()
        layout.addWidget(self.keep_files)
        layout.addWidget(self.keep_folder)
        layout.addWidget(self.keep_config)
        layout.addWidget(self.keep_overlay_keys)

        self.setCentralLayout(layout)

        self.accept_button.setText(self.tr("Uninstall"))
        self.accept_button.setIcon(qta_icon("ri.uninstall-line"))
        self.accept_button.setObjectName("UninstallButton")

        self.keep_files.stateChanged.connect(self.__on_keep_files_changed)

        self.options: UninstallOptionsModel = options

    @pyqtSlot(int)
    def __on_keep_files_changed(self, state: int):
        self.keep_folder.setCheckState(state if state else Qt.CheckState.Checked)
        self.keep_folder.setEnabled(not state)

    def done_handler(self) -> None:
        self.result_ready.emit(self.options)

    def accept_handler(self):
        self.options.set_accepted(
            keep_files=self.keep_files.isChecked(),
            keep_folder=self.keep_folder.isChecked(),
            keep_config=self.keep_config.isChecked(),
            keep_overlay_keys=self.keep_overlay_keys.isChecked(),
        )

    def reject_handler(self):
        self.options.set_rejected()
