import shlex
import shlex
import shutil
from logging import getLogger
from typing import Optional

from PyQt5.QtCore import pyqtSignal, QSize, Qt, QMimeData, pyqtSlot, QCoreApplication
from PyQt5.QtGui import QDrag, QDropEvent, QDragEnterEvent, QDragMoveEvent, QFont, QMouseEvent
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QInputDialog,
    QFrame,
    QMessageBox,
    QSizePolicy,
    QWidget,
    QScrollArea,
    QAction,
    QToolButton,
    QMenu, QDialog,
)

from rare.models.wrapper import Wrapper
from rare.shared import RareCore
from rare.ui.components.tabs.settings.widgets.wrapper import Ui_WrapperSettings
from rare.utils.misc import icon
from rare.utils.runners import proton

logger = getLogger("WrapperSettings")

# extra_wrapper_regex = {
#     "proton": "\".*proton\" run",  # proton
# }


class WrapperDialog(QDialog):
    pass


class WrapperWidget(QFrame):
    # object: current, object: new
    update_wrapper = pyqtSignal(object, object)
    # object: current
    delete_wrapper = pyqtSignal(object)

    def __init__(self, wrapper: Wrapper, parent=None):
        super(WrapperWidget, self).__init__(parent=parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.setToolTip(wrapper.command)

        text_lbl = QLabel(wrapper.name, parent=self)
        text_lbl.setFont(QFont("monospace"))
        text_lbl.setEnabled(wrapper.is_editable)

        image_lbl = QLabel(parent=self)
        image_lbl.setPixmap(icon("mdi.drag-vertical").pixmap(QSize(20, 20)))

        edit_action = QAction("Edit", parent=self)
        edit_action.triggered.connect(self.__edit)
        delete_action = QAction("Delete", parent=self)
        delete_action.triggered.connect(self.__delete)

        manage_menu = QMenu(parent=self)
        manage_menu.addActions([edit_action, delete_action])

        manage_button = QToolButton(parent=self)
        manage_button.setIcon(icon("mdi.menu"))
        manage_button.setMenu(manage_menu)
        manage_button.setPopupMode(QToolButton.InstantPopup)
        manage_button.setEnabled(wrapper.is_editable)
        if not wrapper.is_editable:
            manage_button.setToolTip(self.tr("Manage through settings"))
        else:
            manage_button.setToolTip(self.tr("Manage"))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(image_lbl)
        layout.addWidget(text_lbl)
        layout.addWidget(manage_button)
        self.setLayout(layout)

        self.wrapper = wrapper

        # lk: set object names for the stylesheet
        self.setObjectName(type(self).__name__)
        manage_button.setObjectName(f"{self.objectName()}Button")

    def data(self) -> Wrapper:
        return self.wrapper

    @pyqtSlot()
    def __delete(self) -> None:
        self.delete_wrapper.emit(self.wrapper)
        self.deleteLater()

    @pyqtSlot()
    def __edit(self) -> None:
        dialog = QInputDialog(self)
        dialog.setWindowTitle(f"{self.tr('Edit wrapper')} - {QCoreApplication.instance().applicationName()}")
        dialog.setLabelText(self.tr("Edit wrapper command"))
        dialog.setTextValue(self.wrapper.command)
        accepted = dialog.exec()
        command = dialog.textValue()
        dialog.deleteLater()
        if accepted and command:
            new_wrapper = Wrapper(command=shlex.split(command))
            self.update_wrapper.emit(self.wrapper, new_wrapper)
            self.deleteLater()

    def mouseMoveEvent(self, a0: QMouseEvent) -> None:
        if a0.buttons() == Qt.LeftButton:
            a0.accept()
            if self.wrapper.is_compat_tool:
                return
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)
            drag.exec_(Qt.MoveAction)


class WrapperSettings(QWidget):
    def __init__(self):
        super(WrapperSettings, self).__init__()
        self.ui = Ui_WrapperSettings()
        self.ui.setupUi(self)

        self.wrapper_scroll = QScrollArea(self.ui.widget_stack)
        self.wrapper_scroll.setWidgetResizable(True)
        self.wrapper_scroll.setSizeAdjustPolicy(QScrollArea.AdjustToContents)
        self.wrapper_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.wrapper_scroll.setProperty("no_kinetic_scroll", True)
        self.wrapper_container = WrapperContainer(parent=self.wrapper_scroll)
        self.wrapper_container.orderChanged.connect(self.__on_order_changed)
        self.wrapper_scroll.setWidget(self.wrapper_container)
        self.ui.widget_stack.insertWidget(0, self.wrapper_scroll)

        self.ui.add_button.clicked.connect(self.__on_add_button_pressed)
        self.wrapper_scroll.horizontalScrollBar().rangeChanged.connect(self.adjust_scrollarea)

        # lk: set object names for the stylesheet
        self.setObjectName(type(self).__name__)
        self.ui.no_wrapper_label.setObjectName(f"{self.objectName()}Label")
        self.wrapper_scroll.setObjectName(f"{self.objectName()}Scroll")
        self.wrapper_scroll.horizontalScrollBar().setObjectName(
            f"{self.wrapper_scroll.objectName()}Bar")
        self.wrapper_scroll.verticalScrollBar().setObjectName(
            f"{self.wrapper_scroll.objectName()}Bar")

        self.app_name: str = "default"
        self.core = RareCore.instance().core()
        self.wrappers = RareCore.instance().wrappers()

    @pyqtSlot(int, int)
    def adjust_scrollarea(self, minh: int, maxh: int):
        wrapper_widget = self.wrapper_container.findChild(WrapperWidget)
        if not wrapper_widget:
            return
        # lk: when the scrollbar is not visible, min and max are 0
        if maxh > minh:
            self.wrapper_scroll.setMaximumHeight(
                wrapper_widget.sizeHint().height()
                + self.wrapper_scroll.rect().height() // 2
                - self.wrapper_scroll.contentsRect().height() // 2
                + self.wrapper_container.layout().spacing()
                + self.wrapper_scroll.horizontalScrollBar().sizeHint().height()
            )
        else:
            self.wrapper_scroll.setMaximumHeight(
                wrapper_widget.sizeHint().height()
                + self.wrapper_scroll.rect().height()
                - self.wrapper_scroll.contentsRect().height()
            )

    @pyqtSlot(QWidget, int)
    def __on_order_changed(self, widget: WrapperWidget, new_index: int):
        wrapper = widget.data()
        wrappers = self.wrappers.get_game_wrapper_list(self.app_name)
        wrappers.remove(wrapper)
        wrappers.insert(new_index, wrapper)
        self.wrappers.set_game_wrapper_list(self.app_name, wrappers)

    @pyqtSlot()
    def __on_add_button_pressed(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle(f"{self.tr('Add wrapper')} - {QCoreApplication.instance().applicationName()}")
        dialog.setLabelText(self.tr("Enter wrapper command"))
        accepted = dialog.exec()
        command = dialog.textValue()
        dialog.deleteLater()
        if accepted:
            wrapper = Wrapper(shlex.split(command))
            self.add_user_wrapper(wrapper)

    def __add_wrapper(self, wrapper: Wrapper, position: int = -1):
        self.ui.widget_stack.setCurrentIndex(0)
        widget = WrapperWidget(wrapper, self.wrapper_container)
        if position < 0:
            self.wrapper_container.addWidget(widget)
        else:
            self.wrapper_container.insertWidget(position, widget)
        self.adjust_scrollarea(
            self.wrapper_scroll.horizontalScrollBar().minimum(),
            self.wrapper_scroll.horizontalScrollBar().maximum(),
        )
        widget.update_wrapper.connect(self.__update_wrapper)
        widget.delete_wrapper.connect(self.__delete_wrapper)

    def add_wrapper(self, wrapper: Wrapper, position: int = -1):
        wrappers = self.wrappers.get_game_wrapper_list(self.app_name)
        if position < 0 or wrapper.is_compat_tool:
            wrappers.append(wrapper)
        else:
            wrappers.insert(position, wrapper)
        self.wrappers.set_game_wrapper_list(self.app_name, wrappers)
        self.__add_wrapper(wrapper, position)

    def add_user_wrapper(self, wrapper: Wrapper, position: int = -1):
        if not wrapper:
            return

        compat_cmds = [tool.command() for tool in proton.find_tools()]
        if wrapper.command in compat_cmds:
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("Do not insert compatibility tools manually. Add them through Proton settings"),
            )
            return

        # if text == "mangohud" and self.wrappers.get("mangohud"):
        #     return
        # show_text = ""
        # for key, extra_wrapper in extra_wrapper_regex.items():
        #     if re.match(extra_wrapper, text):
        #         show_text = key
        # if not show_text:
        #     show_text = text.split()[0]

        if wrapper.checksum in self.wrappers.get_game_md5sum_list(self.app_name):
            QMessageBox.warning(
                self, self.tr("Warning"), self.tr("Wrapper <b>{0}</b> is already in the list").format(wrapper.command)
            )
            return

        if not shutil.which(wrapper.executable):
            ans = QMessageBox.question(
                self,
                self.tr("Warning"),
                self.tr("Wrapper <b>{0}</b> is not in $PATH. Add it anyway?").format(wrapper.executable),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if ans == QMessageBox.No:
                return

        self.add_wrapper(wrapper, position)

    @pyqtSlot(object)
    def __delete_wrapper(self, wrapper: Wrapper):
        wrappers = self.wrappers.get_game_wrapper_list(self.app_name)
        wrappers.remove(wrapper)
        self.wrappers.set_game_wrapper_list(self.app_name, wrappers)
        if not wrappers:
            self.wrapper_scroll.setMaximumHeight(self.ui.label_page.sizeHint().height())
            self.ui.widget_stack.setCurrentIndex(1)

    @pyqtSlot(object, object)
    def __update_wrapper(self, old: Wrapper, new: Wrapper):
        wrappers = self.wrappers.get_game_wrapper_list(self.app_name)
        index = wrappers.index(old)
        wrappers.remove(old)
        wrappers.insert(index, new)
        self.wrappers.set_game_wrapper_list(self.app_name, wrappers)
        self.__add_wrapper(new, index)

    @pyqtSlot()
    def update_state(self):
        for w in self.wrapper_container.findChildren(WrapperWidget, options=Qt.FindDirectChildrenOnly):
            w.deleteLater()
        wrappers = self.wrappers.get_game_wrapper_list(self.app_name)
        if not wrappers:
            self.wrapper_scroll.setMaximumHeight(self.ui.label_page.sizeHint().height())
            self.ui.widget_stack.setCurrentIndex(1)
        else:
            self.ui.widget_stack.setCurrentIndex(0)
        for wrapper in wrappers:
            self.__add_wrapper(wrapper)

    def load_settings(self, app_name: str):
        self.app_name = app_name
        self.update_state()


class WrapperContainer(QWidget):
    # QWidget: moving widget, int: new index
    orderChanged: pyqtSignal = pyqtSignal(QWidget, int)

    def __init__(self, parent=None):
        super(WrapperContainer, self).__init__(parent=parent)
        self.setAcceptDrops(True)
        self.__layout = QHBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.__drag_widget: Optional[QWidget] = None

        # lk: set object names for the stylesheet
        self.setObjectName(type(self).__name__)

    # def count(self) -> int:
    #     return self.__layout.count()
    #
    # def itemData(self, index: int) -> Any:
    #     widget: WrapperWidget = self.__layout.itemAt(index).widget()
    #     return widget.data()

    def addWidget(self, widget: WrapperWidget):
        self.__layout.addWidget(widget)

    def insertWidget(self, index: int, widget: WrapperWidget):
        self.__layout.insertWidget(index, widget)

    def dragEnterEvent(self, e: QDragEnterEvent):
        widget = e.source()
        self.__drag_widget = widget
        e.accept()

    def __get_drop_index(self, x) -> int:
        drag_idx = self.__layout.indexOf(self.__drag_widget)

        if drag_idx > 0:
            prev_widget = self.__layout.itemAt(drag_idx - 1).widget()
            if x < self.__drag_widget.x() - prev_widget.width() // 2:
                return drag_idx - 1
        if drag_idx < self.__layout.count() - 1:
            next_widget = self.__layout.itemAt(drag_idx + 1).widget()
            if x > self.__drag_widget.x() + self.__drag_widget.width() + next_widget.width() // 2:
                return drag_idx + 1

        return drag_idx

    def dragMoveEvent(self, e: QDragMoveEvent) -> None:
        new_x = self.__get_drop_index(e.pos().x())
        self.__layout.insertWidget(new_x, self.__drag_widget)

    def dropEvent(self, e: QDropEvent):
        pos = e.pos()
        widget = e.source()
        new_x = self.__get_drop_index(pos.x())
        self.__layout.insertWidget(new_x, widget)
        self.__drag_widget = None
        self.orderChanged.emit(widget, new_x)
        e.accept()
