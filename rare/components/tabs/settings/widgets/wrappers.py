import platform as pf
import shlex
import shutil
from logging import getLogger
from typing import Optional

from PyQt5.QtCore import pyqtSignal, QSize, Qt, QMimeData, pyqtSlot, QCoreApplication
from PyQt5.QtGui import QDrag, QDropEvent, QDragEnterEvent, QDragMoveEvent, QFont, QMouseEvent, QShowEvent
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
    QMenu, QDialog, QStackedWidget, QPushButton,
)

from rare.models.wrapper import Wrapper
from rare.shared import RareCore
from rare.utils.misc import icon

if pf.system() in {"Linux", "FreeBSD"}:
    from rare.utils.runners import proton

logger = getLogger("WrapperSettings")


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
    def __init__(self, parent=None):
        super(WrapperSettings, self).__init__(parent=parent)
        self.widget_stack = QStackedWidget(self)

        self.wrapper_scroll = QScrollArea(self.widget_stack)
        self.wrapper_scroll.setSizeAdjustPolicy(QScrollArea.AdjustToContents)
        self.wrapper_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.wrapper_scroll.setWidgetResizable(True)
        self.wrapper_scroll.setProperty("no_kinetic_scroll", True)
        self.wrapper_container = WrapperContainer(parent=self.wrapper_scroll)
        self.wrapper_container.orderChanged.connect(self.__on_order_changed)
        self.wrapper_scroll.setWidget(self.wrapper_container)

        self.no_wrapper_label = QLabel(self.tr("No wrappers defined"), self.widget_stack)

        self.widget_stack.addWidget(self.wrapper_scroll)
        self.widget_stack.addWidget(self.no_wrapper_label)

        self.add_button = QPushButton(self.tr("Add wrapper"), self)
        self.add_button.clicked.connect(self.__on_add_button_pressed)

        self.wrapper_scroll.horizontalScrollBar().rangeChanged.connect(self.adjust_scrollarea)

        # lk: set object names for the stylesheet
        self.setObjectName("WrapperSettings")
        self.no_wrapper_label.setObjectName(f"{self.objectName()}Label")
        self.wrapper_scroll.setObjectName(f"{self.objectName()}Scroll")
        self.wrapper_scroll.horizontalScrollBar().setObjectName(
            f"{self.wrapper_scroll.objectName()}Bar")
        self.wrapper_scroll.verticalScrollBar().setObjectName(
            f"{self.wrapper_scroll.objectName()}Bar")

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.widget_stack)
        main_layout.addWidget(self.add_button, alignment=Qt.AlignTop)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignTop)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.app_name: str = "default"
        self.core = RareCore.instance().core()
        self.wrappers = RareCore.instance().wrappers()

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        self.update_state()
        return super().showEvent(a0)

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
        self.widget_stack.setCurrentWidget(self.wrapper_scroll)
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

        if pf.system() in {"Linux", "FreeBSD"}:
            compat_cmds = [tool.command() for tool in proton.find_tools()]
            if wrapper.command in compat_cmds:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("Do not insert compatibility tools manually. Add them through Proton settings"),
                )
                return

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
            self.wrapper_scroll.setMaximumHeight(self.no_wrapper_label.sizeHint().height())
            self.widget_stack.setCurrentWidget(self.no_wrapper_label)

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
            self.wrapper_scroll.setMaximumHeight(self.no_wrapper_label.sizeHint().height())
            self.widget_stack.setCurrentWidget(self.no_wrapper_label)
        else:
            self.widget_stack.setCurrentWidget(self.wrapper_scroll)
        for wrapper in wrappers:
            self.__add_wrapper(wrapper)


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
