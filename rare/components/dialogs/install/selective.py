# from logging import getLogger

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QVBoxLayout, QWidget

from rare.models.game import RareEosOverlay, RareGame
from rare.widgets.collapsible_widget import CollapsibleFrame


class InstallTagCheckBox(QCheckBox):
    def __init__(self, text, desc, tags: list[str], *, parent: QWidget | None = None):
        super(InstallTagCheckBox, self).__init__(parent)
        self.setFont(QFont('monospace'))
        self.setText(text)
        self.setToolTip(desc)
        self.tags = tags


class SelectiveWidget(QWidget):
    stateChanged: Signal = Signal()

    def __init__(self, sdl_data: dict, install_tags, disable_sdl, *, parent: QWidget | None = None):
        super().__init__(parent=parent)
        # self.logger = getLogger(type(self).__name__)
        self._has_tags = False

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)

        if not disable_sdl and sdl_data:
            for group, info in sdl_data.items():
                cb = InstallTagCheckBox(info['name'].strip(), info['description'].strip(), info['tags'], parent=self)
                if group == '__required':
                    cb.setChecked(True)
                    cb.setDisabled(True)
                if install_tags is not None:
                    if all(tag in install_tags for tag in info['tags']):
                        cb.setChecked(True)
                cb.stateChanged.connect(self.stateChanged)
                main_layout.addWidget(cb)
            self._has_tags = True
        else:
            self._has_tags = False

    def enabled_tags(self) -> list[str]:
        install_tags = set()
        for cb in self.findChildren(InstallTagCheckBox, options=Qt.FindChildOption.FindDirectChildrenOnly):
            if cb.isChecked():
                install_tags.update(cb.tags)
        install_tags = ['', *install_tags]
        return install_tags

    def supports_tags(self) -> bool:
        return self._has_tags


class InstallDialogSelective(CollapsibleFrame):
    stateChanged: Signal = Signal()

    def __init__(self, rgame: RareGame | RareEosOverlay, *, parent: QWidget | None = None):
        super(InstallDialogSelective, self).__init__(parent=parent)
        # self.logger = getLogger(type(self).__name__)
        title = self.tr('Optional downloads')
        self.setTitle(title)
        self.setEnabled(False)

        self.widget: SelectiveWidget | None = None
        self.rgame = rgame
        self.sdl_data: dict | None = None

    def setup_widget(self, sdl_data: dict):
        self.sdl_data = sdl_data

    def update_widget(self, platform: str):
        platform_sdl = {}
        if self.sdl_data:
            platform_sdl = self.sdl_data[platform]
        install_tags = self.rgame.core.lgd.config.get(self.rgame.app_name, 'install_tags', fallback=None)
        disable_sdl = self.rgame.core.lgd.config.getboolean(self.rgame.app_name, 'disable_sdl', fallback=False)
        if self.widget is not None:
            self.widget.disconnect(self.widget)
            self.widget.deleteLater()
        widget = SelectiveWidget(platform_sdl, install_tags, disable_sdl, parent=self)
        widget.stateChanged.connect(self.stateChanged)
        self.setEnabled(widget.supports_tags())
        self.setWidget(widget)
        self.widget = widget

    def enabled_tags(self) -> list[str]:
        return self.widget.enabled_tags() if self.widget else []


__all__ = ['InstallDialogSelective', 'SelectiveWidget']
