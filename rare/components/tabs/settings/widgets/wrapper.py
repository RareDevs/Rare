import re
import shutil
from logging import getLogger
from typing import Dict

from PyQt5.QtCore import pyqtSignal, QSettings, QSize, Qt, QMimeData
from PyQt5.QtGui import QDrag, QDropEvent, QDragEnterEvent, QDragMoveEvent, QFont
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QInputDialog, QFrame, QMessageBox, QSizePolicy, \
    QWidget

from rare import shared
from rare.ui.components.tabs.settings.wrapper import Ui_WrapperSettings
from rare.utils import config_helper
from rare.utils.utils import icon

logger = getLogger("Wrapper Settings")

extra_wrapper_regex = {
    "proton": "\".*proton\" run",  # proton
    "mangohud": "mangohud"  # mangohud
}


class WrapperWidget(QFrame):
    delete_wrapper = pyqtSignal(str)

    def __init__(self, text: str, parent=None):
        super(WrapperWidget, self).__init__(parent=parent)
        self.setLayout(QHBoxLayout())
        self.text = text
        self.image_lbl = QLabel()
        self.text_lbl = QLabel(text)
        self.text_lbl.setFont(QFont("monospace"))
        self.image_lbl.setPixmap(icon("mdi.drag-vertical").pixmap(QSize(20, 20)))
        self.layout().addWidget(self.image_lbl)
        self.layout().addWidget(self.text_lbl)
        self.setProperty("frameShape", 6)

        self.delete_button = QPushButton(icon("ei.remove"), "")
        self.layout().addWidget(self.delete_button)
        self.delete_button.clicked.connect(self.delete)

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

    def delete(self):
        self.delete_wrapper.emit(self.text)

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)
            drag.exec_(Qt.MoveAction)


class WrapperSettings(QFrame, Ui_WrapperSettings):
    wrappers: Dict[str, WrapperWidget] = dict()
    extra_wrappers: Dict[str, str] = dict()
    app_name: str

    def __init__(self):
        super(WrapperSettings, self).__init__()
        self.setupUi(self)
        self.setProperty("frameShape", 6)
        self.widget_stack.insertWidget(0, self.scroll_area)
        self.placeholder.deleteLater()
        self.scroll_content.deleteLater()
        self.scroll_content = WrapperContainer(
            save_cb=self.save, parent=self.scroll_area)
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setProperty("noBorder", 1)

        self.core = shared.LegendaryCoreSingleton()

        self.add_button.clicked.connect(self.add_button_pressed)
        self.settings = QSettings()

        self.setStyleSheet("""QFrame{padding: 0px}""")

    def get_wrapper_string(self):
        return " ".join(self.get_wrapper_list())

    def get_wrapper_list(self):
        data = list(self.extra_wrappers.values())
        for n in range(self.scroll_content.layout().count()):
            # Get the widget at each index in turn.
            w = self.scroll_content.layout().itemAt(n).widget()
            try:
                data.append(w.text)
            except AttributeError:
                pass
        return data

    def add_button_pressed(self):
        wrapper, done = QInputDialog.getText(self, "Input Dialog", self.tr("Insert name of wrapper"))
        if not done:
            return
        self.add_wrapper(wrapper)

    def add_wrapper(self, text: str, from_load=False):
        for key, extra_wrapper in extra_wrapper_regex.items():
            if re.match(extra_wrapper, text):
                self.extra_wrappers[key] = text
                if not from_load:
                    self.save()
                return

        # validate
        if not text.strip():  # is empty
            return
        if not from_load:
            if self.wrappers.get(text):
                QMessageBox.warning(self, "Warning", self.tr("Wrapper is already in the list"))
                return

            if not shutil.which(text.split()[0]):
                if QMessageBox.question(self, "Warning", self.tr("Wrapper is not in $PATH. Ignore? "),
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.No:
                    return

        self.widget_stack.setCurrentIndex(0)

        widget = WrapperWidget(text, self.scroll_content)
        self.scroll_content.layout().addWidget(widget)
        widget.delete_wrapper.connect(self.delete_wrapper)
        self.scroll_content.layout().addWidget(widget)
        self.wrappers[text] = widget

        if not from_load:
            self.save()

    def delete_wrapper(self, text: str):
        widget = self.wrappers.get(text, None)
        if not widget and self.extra_wrappers.get(text, None):
            self.extra_wrappers.pop(text)
        elif widget:
            widget.deleteLater()
            self.wrappers.pop(text)

        if not self.wrappers:
            self.widget_stack.setCurrentIndex(1)

        self.save()

    def save(self):
        # save wrappers twice, to support wrappers with spaces
        if len(self.wrappers) == 0 and len(self.extra_wrappers) == 0:
            config_helper.remove_option(self.app_name, "wrapper")
            self.settings.remove(f"{self.app_name}/wrapper")
        else:
            config_helper.add_option(self.app_name, "wrapper", self.get_wrapper_string())
            self.settings.setValue(f"{self.app_name}/wrapper", self.get_wrapper_list())

    def load_settings(self, app_name: str):
        self.app_name = app_name
        for i in self.wrappers.values():
            i.deleteLater()
        self.wrappers.clear()
        self.extra_wrappers.clear()

        wrappers = self.settings.value(f"{self.app_name}/wrapper", [], str)

        if not wrappers and (cfg := self.core.lgd.config.get(self.app_name, "wrapper", fallback="")):
            logger.info("Loading wrappers from legendary config")
            # no qt wrapper, but legendary wrapper, to have backward compatibility
            pattern = re.compile(r'''((?:[^ "']|"[^"]*"|'[^']*')+)''')
            wrappers = pattern.split(cfg)[1::2]

        for wrapper in wrappers:
            self.add_wrapper(wrapper, True)

        if not self.wrappers:
            self.widget_stack.setCurrentIndex(1)
        else:
            self.widget_stack.setCurrentIndex(0)
        self.save()


class WrapperContainer(QWidget):
    drag_widget: QWidget

    def __init__(self, save_cb, parent=None):
        super(WrapperContainer, self).__init__(parent=parent)
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setAcceptDrops(True)
        self.save = save_cb

    def dragEnterEvent(self, e: QDragEnterEvent):
        widget = e.source()
        self.drag_widget = widget
        e.accept()

    def _get_drop_index(self, x):
        drag_idx = self.layout().indexOf(self.drag_widget)

        if drag_idx > 0:
            prev_widget = self.layout().itemAt(drag_idx - 1).widget()
            if x < self.drag_widget.x() - prev_widget.width() // 2:
                return drag_idx - 1
        if drag_idx < self.layout().count() - 1:
            next_widget = self.layout().itemAt(drag_idx + 1).widget()
            if x > self.drag_widget.x() + self.drag_widget.width() + next_widget.width() // 2:
                return drag_idx + 1

        return drag_idx

    def dragMoveEvent(self, e: QDragMoveEvent) -> None:
        i = self._get_drop_index(e.pos().x())
        self.layout().insertWidget(i, self.drag_widget)

    def dropEvent(self, e: QDropEvent):
        pos = e.pos()
        widget = e.source()
        index = self._get_drop_index(pos.x())
        self.layout().insertWidget(index, widget)
        self.drag_widget = None
        e.accept()
        self.save()
