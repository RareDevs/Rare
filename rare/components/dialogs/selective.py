from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QVBoxLayout

from rare.models.game import RareGame
from rare.models.install import SelectiveDownloadsModel
from rare.utils.misc import qta_icon
from rare.widgets.dialogs import ButtonDialog, game_title

from .install.selective import SelectiveWidget


class SelectiveDialog(ButtonDialog):
    result_ready = Signal(RareGame, SelectiveDownloadsModel)

    def __init__(self, rgame: RareGame, parent=None):
        super(SelectiveDialog, self).__init__(parent=parent)
        header = self.tr('Optional downloads for')
        self.setWindowTitle(game_title(header, rgame.app_title))
        self.setSubtitle(game_title(header, rgame.app_title))

        sdl_data = rgame.sdl_data(rgame.igame.platform)
        install_tags = rgame.core.lgd.config.get(rgame.app_name, 'install_tags', fallback=None)
        disable_sdl = rgame.core.lgd.config.getboolean(rgame.app_name, 'disable_sdl', fallback=False)
        self.selective_widget = SelectiveWidget(sdl_data, install_tags, disable_sdl, parent=self)

        container = QGroupBox(self.tr('Optional downloads'), self)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.selective_widget)

        layout = QVBoxLayout()
        layout.addWidget(container)

        self.setCentralLayout(layout)

        self.accept_button.setText(self.tr('Verify'))
        self.accept_button.setIcon(qta_icon('fa.check', 'fa5s.check'))

        self.options: SelectiveDownloadsModel = SelectiveDownloadsModel(rgame.app_name)
        self.rgame = rgame

    def done_handler(self):
        self.result_ready.emit(self.rgame, self.options)

    def accept_handler(self):
        self.options.accepted = True
        self.options.install_tag = self.selective_widget.enabled_tags()

    def reject_handler(self):
        self.options.accepted = False
        self.options.install_tag = None
