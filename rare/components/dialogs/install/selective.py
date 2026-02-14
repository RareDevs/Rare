from typing import List, Union

from legendary.utils.selective_dl import get_sdl_appname
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QVBoxLayout, QWidget

from rare.models.game import RareGame
from rare.widgets.collapsible_widget import CollapsibleFrame


class InstallTagCheckBox(QCheckBox):
    def __init__(self, text, desc, tags: List[str], parent=None):
        super(InstallTagCheckBox, self).__init__(parent)
        self.setFont(QFont("monospace"))
        self.setText(text)
        self.setToolTip(desc)
        self.tags = tags

    def isChecked(self) -> Union[bool, List[str]]:
        return self.tags if super(InstallTagCheckBox, self).isChecked() else False


class SelectiveWidget(QWidget):
    stateChanged: Signal = Signal()

    def __init__(self, rgame: RareGame, platform: str, parent=None):
        super().__init__(parent=parent)
        self._has_tags = False

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)

        core = rgame.core

        config_tags = core.lgd.config.get(rgame.app_name, "install_tags", fallback=None)
        config_disable_sdl = core.lgd.config.getboolean(rgame.app_name, "disable_sdl", fallback=False)

        sdl_data = rgame.sdl_data(platform)
        if not config_disable_sdl and sdl_data:
            for group, info in sdl_data.items():
                cb = InstallTagCheckBox(info["name"].strip(), info["description"].strip(), info["tags"])
                if group == "__required":
                    cb.setChecked(True)
                    cb.setDisabled(True)
                if config_tags is not None:
                    if all(tag in config_tags for tag in info["tags"]):
                        cb.setChecked(True)
                cb.stateChanged.connect(self.stateChanged)
                main_layout.addWidget(cb)
            self._has_tags = True
        else:
            self._has_tags = False

    def enabled_tags(self) -> List[str]:
        install_tags = set()
        for cb in self.findChildren(InstallTagCheckBox, options=Qt.FindChildOption.FindDirectChildrenOnly):
            if data := cb.isChecked():
                # noinspection PyTypeChecker
                install_tags.update(data)
        install_tags = ["", *install_tags]
        return install_tags

    def supports_tags(self) -> bool:
        return self._has_tags


class InstallDialogSelective(CollapsibleFrame):
    stateChanged: Signal = Signal()

    def __init__(self, rgame: RareGame, parent=None):
        super(InstallDialogSelective, self).__init__(parent=parent)
        title = self.tr("Optional downloads")
        self.setTitle(title)
        self.setEnabled(False)

        self.widget: SelectiveWidget = None
        self.rgame = rgame

    def update_list(self, platform: str):
        if self.widget is not None:
            self.widget.disconnect(self.widget)
            self.widget.deleteLater()
        self.widget = SelectiveWidget(self.rgame, platform, parent=self)
        self.setEnabled(self.widget.supports_tags())
        self.widget.stateChanged.connect(self.stateChanged)
        self.setWidget(self.widget)

    def enabled_tags(self) -> List[str]:
        return self.widget.enabled_tags()


__all__ = ["InstallDialogSelective", "SelectiveWidget"]
