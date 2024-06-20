import platform as pf
import shlex
import shutil
from logging import getLogger
from typing import Optional, Tuple, Iterable

from PySide6.QtCore import Signal, QSize, Qt, QMimeData, Slot, QObject, QEvent
from PySide6.QtGui import (
    QDrag,
    QDropEvent,
    QDragEnterEvent,
    QDragMoveEvent,
    QFont,
    QAction,
    QMouseEvent,
    QShowEvent,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QFrame,
    QMessageBox,
    QSizePolicy,
    QWidget,
    QScrollArea,
    QMenu,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QComboBox,
)

from rare.models.wrapper import Wrapper
from rare.shared import RareCore
from rare.utils.misc import qta_icon
from rare.widgets.dialogs import ButtonDialog, game_title

if pf.system() in {"Linux", "FreeBSD"}:
    from rare.utils.compat import steam

logger = getLogger("WrapperSettings")


class WrapperEditDialog(ButtonDialog):
    result_ready = Signal(bool, str)

    def __init__(self, parent=None):
        super(WrapperEditDialog, self).__init__(parent=parent)

        self.line_edit = QLineEdit(self)
        self.line_edit.textChanged.connect(self.__on_text_changed)

        self.widget_layout = QVBoxLayout()
        self.widget_layout.addWidget(self.line_edit)

        self.setCentralLayout(self.widget_layout)

        self.accept_button.setText(self.tr("Save"))
        self.accept_button.setIcon(qta_icon("fa.edit"))
        self.accept_button.setEnabled(False)

        self.result: Tuple = ()

    def setup(self, wrapper: Wrapper):
        header = self.tr("Edit wrapper")
        self.setWindowTitle(header)
        self.setSubtitle(game_title(header, wrapper.name))
        self.line_edit.setText(wrapper.as_str)

    @Slot(str)
    def __on_text_changed(self, text: str):
        self.accept_button.setEnabled(bool(text))

    def done_handler(self):
        self.result_ready.emit(*self.result)

    def accept_handler(self):
        self.result = (True, self.line_edit.text())

    def reject_handler(self):
        self.result = (False, self.line_edit.text())


class WrapperAddDialog(WrapperEditDialog):
    def __init__(self, parent=None):
        super(WrapperAddDialog, self).__init__(parent=parent)
        self.combo_box = QComboBox(self)
        self.combo_box.addItem("None", "")
        self.combo_box.currentIndexChanged.connect(self.__on_index_changed)
        self.widget_layout.insertWidget(0, self.combo_box)

    def setup(self, wrappers: Iterable[Wrapper]):
        header = self.tr("Add wrapper")
        self.setWindowTitle(header)
        self.setSubtitle(header)
        for wrapper in wrappers:
            self.combo_box.addItem(f"{wrapper.name} ({wrapper.as_str})", wrapper.as_str)

    @Slot(int)
    def __on_index_changed(self, index: int):
        command = self.combo_box.itemData(index, Qt.ItemDataRole.UserRole)
        self.line_edit.setText(command)


class WrapperWidget(QFrame):
    # object: current, object: new
    update_wrapper = Signal(object, object)
    # object: current
    delete_wrapper = Signal(object)

    def __init__(self, wrapper: Wrapper, parent=None):
        super(WrapperWidget, self).__init__(parent=parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setToolTip(wrapper.as_str)

        text_lbl = QLabel(wrapper.name, parent=self)
        text_lbl.setFont(QFont("monospace"))
        text_lbl.setEnabled(wrapper.is_editable)

        image_lbl = QLabel(parent=self)
        image_lbl.setPixmap(qta_icon("mdi.drag-vertical").pixmap(QSize(20, 20)))

        edit_action = QAction("Edit", parent=self)
        edit_action.triggered.connect(self.__on_edit)
        delete_action = QAction("Delete", parent=self)
        delete_action.triggered.connect(self.__on_delete)

        manage_menu = QMenu(parent=self)
        manage_menu.addActions([edit_action, delete_action])

        manage_button = QPushButton(parent=self)
        manage_button.setIcon(qta_icon("mdi.menu", fallback="fa.align-justify"))
        manage_button.setMenu(manage_menu)
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

    @Slot()
    def __on_delete(self) -> None:
        self.delete_wrapper.emit(self.wrapper)
        self.deleteLater()

    @Slot()
    def __on_edit(self) -> None:
        dialog = WrapperEditDialog(self)
        dialog.setup(self.wrapper)
        dialog.result_ready.connect(self.__on_edit_result)
        dialog.show()

    @Slot(bool, str)
    def __on_edit_result(self, accepted: bool, command: str):
        if accepted and command:
            new_wrapper = Wrapper(command=shlex.split(command))
            self.update_wrapper.emit(self.wrapper, new_wrapper)
            self.deleteLater()

    def mouseMoveEvent(self, a0: QMouseEvent) -> None:
        if a0.buttons() == Qt.MouseButton.LeftButton:
            a0.accept()
            if self.wrapper.is_compat_tool:
                return
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)
            drag.exec_(Qt.DropAction.MoveAction)


class WrapperSettingsScroll(QScrollArea):
    def __init__(self, parent=None):
        super(WrapperSettingsScroll, self).__init__(parent=parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setWidgetResizable(True)
        self.setProperty("no_kinetic_scroll", True)

        self.setObjectName(type(self).__name__)
        self.horizontalScrollBar().setObjectName(f"{self.objectName()}Bar")
        self.verticalScrollBar().setObjectName(f"{self.objectName()}Bar")

    def setWidget(self, w):
        super().setWidget(w)
        w.installEventFilter(self)

    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        if a0 is self.widget() and a1.type() == QEvent.Type.Resize:
            self.__resize(a0)
            return a0.event(a1)
        return False

    def __resize(self, e: QResizeEvent):
        minh = self.horizontalScrollBar().minimum()
        maxh = self.horizontalScrollBar().maximum()
        # lk: when the scrollbar is not visible, min and max are 0
        if maxh > minh:
            height = (
                e.size().height()
                + self.rect().height() // 2
                - self.contentsRect().height() // 2
                + self.widget().layout().spacing()
                + self.horizontalScrollBar().sizeHint().height()
            )
        else:
            height = e.size().height() + self.rect().height() - self.contentsRect().height()
        self.setMaximumHeight(max(height, self.minimumHeight()))


class WrapperSettings(QWidget):
    def __init__(self, parent=None):
        super(WrapperSettings, self).__init__(parent=parent)

        self.wrapper_label = QLabel(self.tr("No wrappers defined"), self)
        self.wrapper_label.setFrameStyle(QLabel.Shape.StyledPanel | QLabel.Shadow.Plain)
        self.wrapper_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.add_button = QPushButton(self.tr("Add wrapper"), self)
        self.add_button.clicked.connect(self.__on_add)

        self.wrapper_scroll = WrapperSettingsScroll(self)
        self.wrapper_scroll.setMinimumHeight(self.add_button.minimumSizeHint().height())

        self.wrapper_container = WrapperContainer(self.wrapper_label, self.wrapper_scroll)
        self.wrapper_container.orderChanged.connect(self.__on_order_changed)
        self.wrapper_scroll.setWidget(self.wrapper_container)

        # lk: set object names for the stylesheet
        self.setObjectName("WrapperSettings")
        self.wrapper_label.setObjectName(f"{self.objectName()}Label")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.wrapper_scroll, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignTop)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.app_name: str = "default"
        self.core = RareCore.instance().core()
        self.wrappers = RareCore.instance().wrappers()

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        self.update_state()
        return super().showEvent(a0)

    @Slot(QWidget, int)
    def __on_order_changed(self, widget: WrapperWidget, new_index: int):
        wrapper = widget.data()
        wrappers = self.wrappers.get_game_wrapper_list(self.app_name)
        wrappers.remove(wrapper)
        wrappers.insert(new_index, wrapper)
        self.wrappers.set_game_wrapper_list(self.app_name, wrappers)

    @Slot()
    def __on_add(self) -> None:
        dialog = WrapperAddDialog(self)
        dialog.setup(self.wrappers.user_wrappers)
        dialog.result_ready.connect(self.__on_add_result)
        dialog.show()

    @Slot(bool, str)
    def __on_add_result(self, accepted: bool, command: str):
        if accepted and command:
            wrapper = Wrapper(shlex.split(command))
            self.add_user_wrapper(wrapper)

    def __add_wrapper(self, wrapper: Wrapper, position: int = -1):
        self.wrapper_label.setVisible(False)
        widget = WrapperWidget(wrapper, self.wrapper_container)
        if position < 0:
            self.wrapper_container.addWidget(widget)
        else:
            self.wrapper_container.insertWidget(position, widget)
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
            compat_cmds = [tool.command() for tool in steam.find_tools()]
            if wrapper.as_str in compat_cmds:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("Do not insert compatibility tools manually. Add them through Proton settings"),
                )
                return

        if wrapper.checksum in self.wrappers.get_game_md5sum_list(self.app_name):
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("Wrapper <b>{0}</b> is already in the list").format(wrapper.as_str),
            )
            return

        if not shutil.which(wrapper.executable):
            ans = QMessageBox.question(
                self,
                self.tr("Warning"),
                self.tr("Wrapper <b>{0}</b> is not in $PATH. Add it anyway?").format(wrapper.executable),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if ans == QMessageBox.StandardButton.No:
                return

        self.add_wrapper(wrapper, position)

    @Slot(object)
    def __delete_wrapper(self, wrapper: Wrapper):
        wrappers = self.wrappers.get_game_wrapper_list(self.app_name)
        wrappers.remove(wrapper)
        self.wrappers.set_game_wrapper_list(self.app_name, wrappers)
        if not wrappers:
            self.wrapper_label.setVisible(True)

    @Slot(object, object)
    def __update_wrapper(self, old: Wrapper, new: Wrapper):
        wrappers = self.wrappers.get_game_wrapper_list(self.app_name)
        index = wrappers.index(old)
        wrappers.remove(old)
        wrappers.insert(index, new)
        self.wrappers.set_game_wrapper_list(self.app_name, wrappers)
        self.__add_wrapper(new, index)

    @Slot()
    def update_state(self):
        for w in self.wrapper_container.findChildren(WrapperWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            w.deleteLater()
        wrappers = self.wrappers.get_game_wrapper_list(self.app_name)
        if not wrappers:
            self.wrapper_label.setVisible(True)
        for wrapper in wrappers:
            self.__add_wrapper(wrapper)


class WrapperContainer(QWidget):
    # QWidget: moving widget, int: new index
    orderChanged: Signal = Signal(QWidget, int)

    def __init__(self, label: QLabel, parent=None):
        super(WrapperContainer, self).__init__(parent=parent)
        self.setAcceptDrops(True)
        self.__layout = QHBoxLayout()
        self.__drag_widget: Optional[QWidget] = None

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(label)
        main_layout.addLayout(self.__layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        main_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)

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
