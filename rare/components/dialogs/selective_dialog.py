from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QGroupBox

from rare.models.game import RareGame
from rare.models.install import SelectiveDownloadsModel
from rare.utils.misc import qta_icon
from rare.widgets.dialogs import ButtonDialog, game_title
from rare.widgets.selective_widget import SelectiveWidget


class SelectiveDialog(ButtonDialog):
    result_ready = Signal(RareGame, SelectiveDownloadsModel)

    def __init__(self, rgame: RareGame, parent=None):
        super(SelectiveDialog, self).__init__(parent=parent)
        header = self.tr("Optional downloads for")
        self.setWindowTitle(game_title(header, rgame.app_title))
        self.setSubtitle(game_title(header, rgame.app_title))

        self.rgame = rgame
        self.selective_widget = SelectiveWidget(rgame, rgame.igame.platform, self)

        container = QGroupBox(self.tr("Optional downloads"), self)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.selective_widget)

        layout = QVBoxLayout()
        layout.addWidget(container)

        self.setCentralLayout(layout)

        self.accept_button.setText(self.tr("Verify"))
        self.accept_button.setIcon(qta_icon("fa.check"))

        self.options: SelectiveDownloadsModel = SelectiveDownloadsModel(rgame.app_name)

    def done_handler(self):
        self.result_ready.emit(self.rgame, self.options)

    def accept_handler(self):
        self.options.accepted = True
        self.options.install_tag = self.selective_widget.install_tags()

    def reject_handler(self):
        self.options.accepted = False
        self.options.install_tag = None
