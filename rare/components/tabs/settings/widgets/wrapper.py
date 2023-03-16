import re
import shutil
from logging import getLogger
from typing import Dict, List

from PyQt5.QtCore import pyqtSignal, QSettings, QSize, Qt, QMimeData, pyqtSlot, QCoreApplication
from PyQt5.QtGui import QDrag, QDropEvent, QDragEnterEvent, QDragMoveEvent, QFont
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QInputDialog,
    QFrame,
    QMessageBox,
    QSizePolicy,
    QWidget,
    QScrollArea,
)

from rare.shared import RareCore
from rare.ui.components.tabs.settings.widgets.wrapper import Ui_WrapperSettings
from rare.utils import config_helper
from rare.utils.misc import icon

logger = getLogger("WrapperSettings")

extra_wrapper_regex = {
    "proton": "\".*proton\" run",  # proton
    "mangohud": "mangohud"  # mangohud
}


class WrapperWidget(QFrame):
    delete_wrapper = pyqtSignal(str)

    def __init__(self, text: str, show_text=None, parent=None):
        super(WrapperWidget, self).__init__(parent=parent)
        if not show_text:
            show_text = text

        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        self.text = text
        self.text_lbl = QLabel(show_text, parent=self)
        self.text_lbl.setFont(QFont("monospace"))
        self.image_lbl = QLabel(parent=self)
        self.image_lbl.setPixmap(icon("mdi.drag-vertical").pixmap(QSize(20, 20)))

        self.delete_button = QPushButton(icon("ei.remove"), "", parent=self)
        if show_text in extra_wrapper_regex.keys():
            self.delete_button.setDisabled(True)
            self.delete_button.setToolTip(self.tr("Disable it in settings"))
        self.delete_button.clicked.connect(self.delete)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.image_lbl)
        layout.addWidget(self.text_lbl)
        layout.addWidget(self.delete_button)
        self.setLayout(layout)

        # lk: set object names for the stylesheet
        self.setObjectName(type(self).__name__)
        self.delete_button.setObjectName(f"{self.objectName()}Button")

    def delete(self):
        self.delete_wrapper.emit(self.text)

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)
            drag.exec_(Qt.MoveAction)


class WrapperSettings(QWidget, Ui_WrapperSettings):
    def __init__(self):
        super(WrapperSettings, self).__init__()
        self.setupUi(self)

        self.wrappers: Dict[str, WrapperWidget] = {}
        self.app_name: str

        self.wrapper_scroll = QScrollArea(self.widget_stack)
        self.wrapper_scroll.setWidgetResizable(True)
        self.wrapper_scroll.setSizeAdjustPolicy(QScrollArea.AdjustToContents)
        self.wrapper_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.wrapper_scroll.setProperty("no_kinetic_scroll", True)
        self.scroll_content = WrapperContainer(
            save_cb=self.save, parent=self.wrapper_scroll
        )
        self.wrapper_scroll.setWidget(self.scroll_content)
        self.widget_stack.insertWidget(0, self.wrapper_scroll)

        self.core = RareCore.instance().core()

        self.add_button.clicked.connect(self.add_button_pressed)
        self.settings = QSettings()

        self.wrapper_scroll.horizontalScrollBar().rangeChanged.connect(self.adjust_scrollarea)

        # lk: set object names for the stylesheet
        self.setObjectName(type(self).__name__)
        self.no_wrapper_label.setObjectName(f"{self.objectName()}Label")
        self.wrapper_scroll.setObjectName(f"{self.objectName()}Scroll")
        self.wrapper_scroll.horizontalScrollBar().setObjectName(
            f"{self.wrapper_scroll.objectName()}Bar")
        self.wrapper_scroll.verticalScrollBar().setObjectName(
            f"{self.wrapper_scroll.objectName()}Bar")

    @pyqtSlot(int, int)
    def adjust_scrollarea(self, min: int, max: int):
        wrapper_widget = self.scroll_content.findChild(WrapperWidget)
        if not wrapper_widget:
             return
        # lk: when the scrollbar is not visible, min and max are 0
        if max > min:
            self.wrapper_scroll.setMaximumHeight(
                wrapper_widget.sizeHint().height()
                + self.wrapper_scroll.rect().height() // 2
                - self.wrapper_scroll.contentsRect().height() // 2
                + self.scroll_content.layout().spacing()
                + self.wrapper_scroll.horizontalScrollBar().sizeHint().height()
            )
        else:
            self.wrapper_scroll.setMaximumHeight(
                wrapper_widget.sizeHint().height()
                + self.wrapper_scroll.rect().height()
                - self.wrapper_scroll.contentsRect().height()
            )

    def get_wrapper_string(self):
        return " ".join(self.get_wrapper_list())

    def get_wrapper_list(self):
        data: List[str] = []
        for w in self.wrappers.values():
            # Get the widget at each index in turn.
            try:
                data.append(w.text)
            except AttributeError:
                pass
        return data

    def add_button_pressed(self):
        header = self.tr("Add wrapper")
        wrapper, done = QInputDialog.getText(
            self, f"{header} - {QCoreApplication.instance().applicationName()}", self.tr("Insert wrapper executable")
        )
        if not done:
            return
        self.add_wrapper(wrapper)

    def add_wrapper(self, text: str, from_load=False):
        if text == "mangohud" and self.wrappers.get("mangohud"):
            return
        show_text = text
        for key, extra_wrapper in extra_wrapper_regex.items():
            if re.match(extra_wrapper, text):
                show_text = key

        # validate
        if not text.strip():  # is empty
            return
        if not from_load:
            if self.wrappers.get(text):
                QMessageBox.warning(self, "Warning", self.tr("Wrapper is already in the list"))
                return

            if show_text != "proton" and not shutil.which(text.split()[0]):
                if QMessageBox.question(self, "Warning", self.tr("Wrapper is not in $PATH. Ignore? "),
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.No:
                    return

            if text == "proton":
                QMessageBox.warning(self, "Warning", self.tr("Do not insert proton manually. Add it in proton settings"))
                return

        self.widget_stack.setCurrentIndex(0)

        if widget := self.wrappers.get(show_text, None):
            widget.deleteLater()

        widget = WrapperWidget(text, show_text, self.scroll_content)
        self.scroll_content.layout().addWidget(widget)
        self.adjust_scrollarea(
            self.wrapper_scroll.horizontalScrollBar().minimum(),
            self.wrapper_scroll.horizontalScrollBar().maximum()
        )
        widget.delete_wrapper.connect(self.delete_wrapper)
        self.wrappers[show_text] = widget

        if not from_load:
            self.save()

    def delete_wrapper(self, text: str):
        widget = self.wrappers.get(text, None)
        if widget:
            self.wrappers.pop(text)
            widget.deleteLater()

        if not self.wrappers:
            self.wrapper_scroll.setMaximumHeight(self.label_page.sizeHint().height())
            self.widget_stack.setCurrentIndex(1)

        self.save()

    def save(self):
        # save wrappers twice, to support wrappers with spaces
        if len(self.wrappers) == 0:
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

        wrappers = self.settings.value(f"{self.app_name}/wrapper", [], str)

        if not wrappers and (cfg := self.core.lgd.config.get(self.app_name, "wrapper", fallback="")):
            logger.info("Loading wrappers from legendary config")
            # no qt wrapper, but legendary wrapper, to have backward compatibility
            pattern = re.compile(r'''((?:[^ "']|"[^"]*"|'[^']*')+)''')
            wrappers = pattern.split(cfg)[1::2]

        for wrapper in wrappers:
            self.add_wrapper(wrapper, True)

        if not self.wrappers:
            self.wrapper_scroll.setMaximumHeight(self.label_page.sizeHint().height())
            self.widget_stack.setCurrentIndex(1)
        else:
            self.widget_stack.setCurrentIndex(0)

        self.save()


class WrapperContainer(QWidget):
    drag_widget: QWidget

    def __init__(self, save_cb, parent=None):
        super(WrapperContainer, self).__init__(parent=parent)
        self.setAcceptDrops(True)
        self.save = save_cb
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setLayout(layout)

        # lk: set object names for the stylesheet
        self.setObjectName(type(self).__name__)

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
