from typing import List, Union, Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QCheckBox,
    QLayout, QGroupBox,
)
from legendary.utils.selective_dl import get_sdl_appname

from rare.models.game import RareGame
from rare.models.install import SelectiveDownloadsModel
from rare.widgets.dialogs import ButtonDialog, dialog_title_game
from rare.utils.misc import icon


class SelectiveDialog(ButtonDialog):
    result_ready = pyqtSignal(RareGame, SelectiveDownloadsModel)

    def __init__(self, rgame: RareGame, parent=None):
        super(SelectiveDialog, self).__init__(parent=parent)
        header = self.tr("Optional downloads for")
        self.setWindowTitle(dialog_title_game(header, rgame.app_title))

        title_label = QLabel(f"<h4>{dialog_title_game(header, rgame.app_title)}</h4>", self)

        self.core = rgame.core
        self.rgame = rgame

        selectable_group = QGroupBox(self.tr("Optional downloads"), self)
        self.selectable_layout = QVBoxLayout(selectable_group)
        self.selectable_layout.setSpacing(0)

        self.selectable_checks: List[TagCheckBox] = []
        self.config_tags: Optional[List[str]] = None

        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetFixedSize)
        layout.addWidget(title_label)
        layout.addWidget(selectable_group)

        self.setCentralLayout(layout)

        self.accept_button.setText(self.tr("Verify"))
        self.accept_button.setIcon(icon("fa.check"))

        self.options: SelectiveDownloadsModel = SelectiveDownloadsModel(rgame.app_name)

        config_disable_sdl = self.core.lgd.config.getboolean(self.rgame.app_name, "disable_sdl", fallback=False)
        sdl_name = get_sdl_appname(self.rgame.app_name)
        if not config_disable_sdl and sdl_name is not None:
            self.create_sdl_list()
        else:
            self.options.accepted = True
            self.accept()

    def create_sdl_list(self):
        platform = self.rgame.igame.platform
        for cb in self.selectable_checks:
            cb.disconnect()
            cb.deleteLater()
        self.selectable_checks.clear()

        if config_tags := self.core.lgd.config.get(self.rgame.app_name, "install_tags", fallback=None):
            self.config_tags = config_tags.split(",")
        config_disable_sdl = self.core.lgd.config.getboolean(self.rgame.app_name, "disable_sdl", fallback=False)
        sdl_name = get_sdl_appname(self.rgame.app_name)
        if not config_disable_sdl and sdl_name is not None:
            sdl_data = self.core.get_sdl_data(sdl_name, platform=platform)
            if sdl_data:
                for tag, info in sdl_data.items():
                    cb = TagCheckBox(info["name"].strip(), info["description"].strip(), info["tags"])
                    if tag == "__required":
                        cb.setChecked(True)
                        cb.setDisabled(True)
                    if self.config_tags is not None:
                        if all(elem in self.config_tags for elem in info["tags"]):
                            cb.setChecked(True)
                    self.selectable_layout.addWidget(cb)
                    self.selectable_checks.append(cb)

    def done_handler(self):
        self.result_ready.emit(self.rgame, self.options)

    def accept_handler(self):
        install_tag = [""]
        for cb in self.selectable_checks:
            if data := cb.isChecked():
                # noinspection PyTypeChecker
                install_tag.extend(data)
        self.options.accepted = True
        self.options.install_tag = install_tag

    def reject_handler(self):
        self.options.accepted = False
        self.options.install_tag = None


class TagCheckBox(QCheckBox):
    def __init__(self, text, desc, tags: List[str], parent=None):
        super(TagCheckBox, self).__init__(parent)
        self.setText(text)
        self.setToolTip(desc)
        self.tags = tags

    def isChecked(self) -> Union[bool, List[str]]:
        return self.tags if super(TagCheckBox, self).isChecked() else False
