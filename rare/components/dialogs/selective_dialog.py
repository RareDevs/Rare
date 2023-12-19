from typing import List, Union, Optional

from PyQt5.QtCore import Qt, pyqtSignal, QCoreApplication
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QCheckBox,
    QHBoxLayout,
    QPushButton,
    QLayout, QGroupBox,
)
from legendary.utils.selective_dl import get_sdl_appname

from rare.models.game import RareGame
from rare.models.install import SelectiveDownloadsModel


class SelectiveDownloadsDialog(QDialog):
    result_ready = pyqtSignal(RareGame, SelectiveDownloadsModel)

    def __init__(self, rgame: RareGame, parent=None):
        super(SelectiveDownloadsDialog, self).__init__(parent=parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        header = self.tr("Optional downloads for")
        self.setWindowTitle(f'{header} "{rgame.app_title}" - {QCoreApplication.instance().applicationName()}')
        self.title_label = QLabel(
            self.tr("<h4>Select the optional downloads for <b>{}</b> to verify with.</h4>").format(rgame.app_title)
        )

        self.core = rgame.core
        self.rgame = rgame

        self.selectable = QGroupBox(self.tr("Optional downloads"), self)
        self.selectable_layout = QVBoxLayout(self.selectable)
        self.selectable_layout.setSpacing(0)

        self.selectable_checks: List[TagCheckBox] = []
        self.config_tags: Optional[List[str]] = None

        self.verify_button = QPushButton(self.tr("Verify"))
        self.verify_button.clicked.connect(self.__on_verify)

        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.__on_cancel)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.verify_button)

        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        layout.addWidget(self.title_label)
        layout.addWidget(self.selectable)
        layout.addLayout(button_layout)

        self.options: SelectiveDownloadsModel = SelectiveDownloadsModel(rgame.app_name)

        config_disable_sdl = self.core.lgd.config.getboolean(self.rgame.app_name, "disable_sdl", fallback=False)
        sdl_name = get_sdl_appname(self.rgame.app_name)
        if not config_disable_sdl and sdl_name is not None:
            self.reset_sdl_list()
        else:
            self.options.accepted = True
            self.close()

    def reset_sdl_list(self):
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
                # for cb in self.selectable_checks:
                #     cb.stateChanged.connect(self.option_changed)
                # self.selectable.setWidget(widget)
        else:
            self.selectable.setDisabled(True)

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.result_ready.emit(self.rgame, self.options)
        super(SelectiveDownloadsDialog, self).closeEvent(a0)

    def __on_verify(self):
        install_tag = [""]
        for cb in self.selectable_checks:
            if data := cb.isChecked():
                # noinspection PyTypeChecker
                install_tag.extend(data)
        self.options.accepted = True
        self.options.install_tag = install_tag
        self.close()

    def __on_cancel(self):
        self.options.accepted = False
        self.options.install_tag = None
        self.close()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key_Escape:
            e.accept()
            self.__on_cancel()


class TagCheckBox(QCheckBox):
    def __init__(self, text, desc, tags: List[str], parent=None):
        super(TagCheckBox, self).__init__(parent)
        self.setText(text)
        self.setToolTip(desc)
        self.tags = tags

    def isChecked(self) -> Union[bool, List[str]]:
        return self.tags if super(TagCheckBox, self).isChecked() else False
