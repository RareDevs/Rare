import re
from logging import getLogger
from typing import Dict

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton, QInputDialog, QFrame, QWidget

from rare import shared
from rare.ui.components.tabs.settings.wrapper import Ui_WrapperSettings
from rare.utils import config_helper
from rare.utils.extra_widgets import FlowLayout
from rare.utils.utils import icon

logger = getLogger("Wrapper Settings")

extra_wrapper_regex = {
    "proton": "\".*proton\" run",  # proton
    "mangohud": "mangohud"  # mangohud
}


class WrapperWidget(QGroupBox):
    delete_wrapper = pyqtSignal(str)

    def __init__(self, text: str):
        super(WrapperWidget, self).__init__()
        self.setLayout(QHBoxLayout())
        self.text = text
        self.layout().addWidget(QLabel(text))

        self.delete_button = QPushButton(icon("ei.remove"), "")
        self.layout().addWidget(self.delete_button)
        self.delete_button.clicked.connect(self.delete)

    def delete(self):
        self.delete_wrapper.emit(self.text)


class WrapperSettings(QGroupBox, Ui_WrapperSettings):
    wrappers: Dict[str, WrapperWidget] = dict()
    extra_wrappers: Dict[str, str] = dict()
    app_name: str

    def __init__(self):
        super(WrapperSettings, self).__init__("Wrapper")
        self.setupUi(self)
        self.widgets.setLayout(FlowLayout())
        self.core = shared.LegendaryCoreSingleton()

        self.add_button.clicked.connect(self.add_button_pressed)

    def get_wrapper_string(self):
        return " ".join(list(self.extra_wrappers.values()) + list(self.wrappers.keys()))

    def add_button_pressed(self):
        wrapper, done = QInputDialog.getText(self, "Input Dialog", self.tr("Insert name of wrapper"))
        if not done:
            return
        self.add_wrapper(wrapper)

    def add_wrapper(self, text: str):
        for key, extra_wrapper in extra_wrapper_regex.items():
            if re.match(extra_wrapper, text):
                self.extra_wrappers[key] = text
                self.save()
                return
        widget = WrapperWidget(text)
        widget.delete_wrapper.connect(self.delete_wrapper)
        self.widgets.layout().addWidget(widget)
        self.wrappers[text] = widget
        self.widget_stack.setCurrentIndex(0)

        # flow layout bug
        self.widgets.update()
        self.save()

    def delete_wrapper(self, text: str):
        widget = self.wrappers.get(text, None)
        if not widget and self.extra_wrappers.get(text, None):
            self.extra_wrappers.pop(text)
        elif widget:
            widget.deleteLater()
            self.wrappers.pop(text)

        if self.wrappers:
            self.widget_stack.setCurrentIndex(1)
        self.save()

    def save(self):
        if len(self.wrappers) == 0 and len(self.extra_wrappers) == 0:
            config_helper.remove_option(self.app_name, "wrapper")
        else:
            config_helper.add_option(self.app_name, "wrapper", self.get_wrapper_string())

    def load_settings(self, app_name):
        self.app_name = app_name
        for i in self.wrappers.values():
            i.deleteLater()
        self.wrappers.clear()
        self.extra_wrappers.clear()

        wrapper_config = self.core.lgd.config.get(app_name, "wrapper", fallback="")
        pattern = re.compile(r'''((?:[^ "']|"[^"]*"|'[^']*')+)''')
        wrappers = pattern.split(wrapper_config)[1::2]
        if not wrappers:
            self.widget_stack.setCurrentIndex(1)
            return
        else:
            self.widget_stack.setCurrentIndex(0)

        for wrapper in wrappers:
            if wrapper.strip('"').endswith("proton"):
                wrapper = f"{wrapper} run"
            if wrapper == "run":
                continue
            self.add_wrapper(wrapper)
