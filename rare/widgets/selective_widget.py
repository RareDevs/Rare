from typing import List, Union

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QWidget, QVBoxLayout
from legendary.utils.selective_dl import get_sdl_appname

from rare.models.game import RareGame


class TagCheckBox(QCheckBox):
    def __init__(self, text, desc, tags: List[str], parent=None):
        super(TagCheckBox, self).__init__(parent)
        self.setText(text)
        self.setToolTip(desc)
        self.tags = tags

    def isChecked(self) -> Union[bool, List[str]]:
        return self.tags if super(TagCheckBox, self).isChecked() else False


class SelectiveWidget(QWidget):
    stateChanged: Signal = Signal()

    def __init__(self, rgame: RareGame, platform: str, parent=None):
        super().__init__(parent=parent)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)

        core = rgame.core

        config_tags = core.lgd.config.get(rgame.app_name, "install_tags", fallback=None)
        config_disable_sdl = core.lgd.config.getboolean(rgame.app_name, "disable_sdl", fallback=False)
        sdl_name = get_sdl_appname(rgame.app_name)
        if not config_disable_sdl and sdl_name is not None:
            sdl_data = core.get_sdl_data(sdl_name, platform=platform)
            if sdl_data:
                for tag, info in sdl_data.items():
                    cb = TagCheckBox(info["name"].strip(), info["description"].strip(), info["tags"])
                    if tag == "__required":
                        cb.setChecked(True)
                        cb.setDisabled(True)
                    if config_tags is not None:
                        if all(elem in config_tags for elem in info["tags"]):
                            cb.setChecked(True)
                    cb.stateChanged.connect(self.stateChanged)
                    main_layout.addWidget(cb)
            self.parent().setDisabled(False)
        else:
            self.parent().setDisabled(True)

    def install_tags(self):
        install_tags = [""]
        for cb in self.findChildren(TagCheckBox, options=Qt.FindChildOption.FindDirectChildrenOnly):
            if data := cb.isChecked():
                # noinspection PyTypeChecker
                install_tags.extend(data)
        return install_tags
