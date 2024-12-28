import os
from enum import IntEnum, Enum
from logging import getLogger
from typing import Callable, Tuple, Optional, Dict, List

from PySide6.QtCore import (
    QSize,
    Signal,
    QFileInfo,
    QRunnable,
    QObject,
    QThreadPool,
    Slot,
    QDir,
)
from PySide6.QtGui import QAbstractFileIconProvider
from PySide6.QtWidgets import (
    QSizePolicy,
    QLabel,
    QFileDialog,
    QHBoxLayout,
    QWidget,
    QLineEdit,
    QCompleter,
    QFileSystemModel,
    QStyledItemDelegate,
    QPushButton,
)

from rare.utils.misc import qta_icon

logger = getLogger("IndicatorEdit")


class IndicatorReasonsCommon(IntEnum):
    VALID = 0
    UNDEFINED = 1
    EMPTY = 2
    WRONG_FORMAT = 3
    WRONG_PATH = 4
    DIR_NOT_EMPTY = 5
    DIR_NOT_EXISTS = 6
    FILE_NOT_EXISTS = 7
    GAME_NOT_INSTALLED = 8
    GAME_NOT_EXISTS = 9


class IndicatorReasons(IntEnum):
    """
    Empty enumeration with auto-generated enumeration values.
    Extend this class per-case to implement dedicated message types.
    Types should be assigned using `auto()` from enum

    example:
    MyReasons(IndicatorReasons):
        MY_REASON = auto()
    """
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        """generate consecutive automatic numbers starting from zero"""
        start = len(IndicatorReasonsCommon)
        return IntEnum._generate_next_value_(name, start, count, last_values)


class IndicatorReasonsStrings(QObject):
    def __init__(self, parent=None):
        super(IndicatorReasonsStrings, self).__init__(parent=parent)
        self.__text = {
            IndicatorReasonsCommon.VALID: self.tr("Ok!"),
            IndicatorReasonsCommon.UNDEFINED: self.tr("Unknown error occurred"),
            IndicatorReasonsCommon.EMPTY: self.tr("Value can not be empty"),
            IndicatorReasonsCommon.WRONG_FORMAT: self.tr("Wrong format"),
            IndicatorReasonsCommon.WRONG_PATH: self.tr("Wrong file or directory"),
            IndicatorReasonsCommon.DIR_NOT_EMPTY: self.tr("Directory is not empty"),
            IndicatorReasonsCommon.DIR_NOT_EXISTS: self.tr("Directory does not exist"),
            IndicatorReasonsCommon.FILE_NOT_EXISTS: self.tr("File does not exist"),
            IndicatorReasonsCommon.GAME_NOT_INSTALLED: self.tr("Game is not installed"),
            IndicatorReasonsCommon.GAME_NOT_EXISTS: self.tr("Game does not exist"),
        }

    def __getitem__(self, item: int) -> str:
        return self.__text[item]

    def __setitem__(self, key: int, value: str):
        self.__text[key] = value

    def extend(self, reasons: Dict):
        for k in self.__text.keys():
            if k in reasons.keys():
                raise RuntimeError(f"{reasons} contains existing values")
        self.__text.update(reasons)


class EditFuncRunnable(QRunnable):
    class Signals(QObject):
        result = Signal(bool, str, int)

    def __init__(self, func: Callable[[str], Tuple[bool, str, int]], args: str):
        super(EditFuncRunnable, self).__init__()
        self.setAutoDelete(True)
        self.signals = EditFuncRunnable.Signals()
        self.func = self.__wrap_edit_function(func)
        self.args = args

    def run(self):
        o0, o1, o2 = self.func(self.args)
        self.signals.result.emit(o0, o1, o2)
        self.signals.deleteLater()

    @staticmethod
    def __wrap_edit_function(func: Callable[[str], Tuple[bool, str, int]]):
        if func:
            return lambda text: func(os.path.expanduser(text) if text.startswith("~") else text)
        else:
            return func


class IndicatorLineEdit(QWidget):
    textChanged = Signal(str)

    def __init__(
        self,
        text: str = "",
        placeholder: str = "",
        completer: QCompleter = None,
        edit_func: Callable[[str], Tuple[bool, str, int]] = None,
        save_func: Callable[[str], None] = None,
        horiz_policy: QSizePolicy.Policy = QSizePolicy.Policy.Expanding,
        parent=None,
    ):
        super(IndicatorLineEdit, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        layout = QHBoxLayout(self)
        layout.setObjectName(f"{self.objectName()}Layout")
        layout.setContentsMargins(0, 0, 0, 0)
        # Add line_edit
        self.line_edit = QLineEdit(self)
        self.line_edit.setObjectName(f"{type(self).__name__}Edit")
        self.line_edit.setPlaceholderText(placeholder if placeholder else self.tr("Use global/default settings"))
        self.line_edit.setToolTip(placeholder if placeholder else "")
        self.line_edit.setSizePolicy(horiz_policy, QSizePolicy.Policy.Fixed)
        # Add completer
        self.setCompleter(completer)
        layout.addWidget(self.line_edit)
        if edit_func is not None:
            self.indicator_label = QLabel(self)
            self.indicator_label.setPixmap(qta_icon("ei.info-circle", color="gray").pixmap(16, 16))
            self.indicator_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            layout.addWidget(self.indicator_label)

        self.__reasons = IndicatorReasonsStrings(self)

        self.__threadpool = QThreadPool(self)
        self.__threadpool.setMaxThreadCount(1)
        self.__thread: Optional[EditFuncRunnable] = None

        self.is_valid = False
        self.edit_func = edit_func
        self.save_func = save_func
        if text:
            self.line_edit.setText(text)
        self.line_edit.textChanged.connect(self.__edit)
        if self.edit_func is None:
            self.line_edit.textChanged.connect(self.__save)

        # lk: this can be placed here to trigger __edit
        # lk: it is going to save the input again if it is valid which
        # lk: is ok to do given the checks don't misbehave (they shouldn't)
        # lk: however it is going to edit any "understood" bad input to good input
        # lk: and we might not want that (but the validity check reports on the edited string)
        # lk: it is also going to trigger this widget's textChanged signal but that gets lost
        # if text:
        #     self.line_edit.setText(text)

    def deleteLater(self) -> None:
        if self.__thread is not None:
            self.__thread.signals.result.disconnect()
        super(IndicatorLineEdit, self).deleteLater()

    def text(self) -> str:
        return self.line_edit.text()

    def setText(self, text: str):
        self.line_edit.setText(text)

    def setCompleter(self, completer: Optional[QCompleter]):
        if old := self.line_edit.completer():
            old.deleteLater()
        if not completer:
            self.line_edit.setCompleter(None)
            return
        completer.popup().setItemDelegate(QStyledItemDelegate(self))
        completer.popup().setAlternatingRowColors(True)
        self.line_edit.setCompleter(completer)

    def extend_reasons(self, reasons: Dict):
        self.__reasons.extend(reasons)

    def __indicator(self, valid, reason: int = 0):
        color = "green" if valid else "red"
        self.indicator_label.setPixmap(qta_icon("ei.info-circle", color=color).pixmap(16, 16))
        if not valid:
            self.indicator_label.setToolTip(self.__reasons[reason])
        else:
            self.indicator_label.setToolTip(self.__reasons[IndicatorReasonsCommon.VALID])

    @Slot(bool, str, int)
    def __edit_handler(self, is_valid: bool, text: str, reason: int):
        self.__thread = None
        self.line_edit.blockSignals(True)
        if text != self.line_edit.text():
            self.line_edit.setText(text)
        self.line_edit.blockSignals(False)
        self.__indicator(is_valid, reason)
        if is_valid:
            self.__save(text)
        self.is_valid = is_valid
        self.textChanged.emit(text)

    def __edit(self, text):
        if self.edit_func is not None:
            if self.__thread is not None:
                self.__thread.signals.result.disconnect(self.__edit_handler)
            self.__thread = EditFuncRunnable(self.edit_func, text)
            self.__thread.signals.result.connect(self.__edit_handler)
            self.__threadpool.start(self.__thread)

    def __save(self, text):
        if self.save_func is not None:
            self.save_func(text)


class PathEditIconProvider(QAbstractFileIconProvider):
    class CustomIconType(Enum):
        Unknown = -1
        Executable = -2

    icons = {
        CustomIconType.Unknown: ("mdi.file-cancel", "fa.file-excel-o"),  # Unknown
        QAbstractFileIconProvider.IconType.Computer: ("mdi.desktop-classic", "fa.desktop"),  # Computer
        QAbstractFileIconProvider.IconType.Desktop: ("mdi.desktop-mac", "fa.desktop"),  # Desktop
        QAbstractFileIconProvider.IconType.Trashcan: ("mdi.trash-can", "fa.trash"),  # Trashcan
        QAbstractFileIconProvider.IconType.Network: ("mdi.server-network", "fa.server"),  # Network
        QAbstractFileIconProvider.IconType.Drive: ("mdi.harddisk", "fa.desktop"),  # Drive
        QAbstractFileIconProvider.IconType.Folder: ("mdi.folder", "fa.folder"),  # Folder
        QAbstractFileIconProvider.IconType.File: ("mdi.file", "fa.file"),  # File
        CustomIconType.Executable: ("mdi.cog", "fa.cog"),  # Executable
    }

    def __init__(self):
        super(PathEditIconProvider, self).__init__()
        self.setOptions(QAbstractFileIconProvider.Option.DontUseCustomDirectoryIcons)
        self.icon_types = {}
        for idx, (icn, fallback) in PathEditIconProvider.icons.items():
            self.icon_types.update({idx: qta_icon(icn, fallback, color="#eeeeee")})

    def icon(self, info_type):
        if isinstance(info_type, QFileInfo):
            if info_type.isRoot():
                return self.icon_types[QAbstractFileIconProvider.IconType.Drive]
            if info_type.isDir():
                return self.icon_types[QAbstractFileIconProvider.IconType.Folder]
            if info_type.isFile():
                return self.icon_types[QAbstractFileIconProvider.IconType.File]
            if info_type.isExecutable():
                return self.icon_types[PathEditIconProvider.CustomIconType.Executable]
            return self.icon_types[PathEditIconProvider.CustomIconType.Unknown]
        return self.icon_types[info_type]


class PathEdit(IndicatorLineEdit):
    def __init__(
        self,
        path: str = "",
        file_mode: QFileDialog.FileMode = QFileDialog.FileMode.AnyFile,
        file_filter: QDir.Filter = 0,
        name_filters: Tuple[str, ...] = None,
        placeholder: str = "",
        edit_func: Callable[[str], Tuple[bool, str, int]] = None,
        save_func: Callable[[str], None] = None,
        horiz_policy: QSizePolicy.Policy = QSizePolicy.Policy.Expanding,
        parent=None,
    ):
        self.__root_path = path if path else os.path.expanduser("~/")
        self.__completer = QCompleter()
        self.__completer_model = QFileSystemModel(self.__completer)
        try:
            self.__completer_model.setOptions(
                QFileSystemModel.Option.DontWatchForChanges
                | QFileSystemModel.Option.DontResolveSymlinks
                | QFileSystemModel.Option.DontUseCustomDirectoryIcons
            )
        except AttributeError as e:  # Error on Ubuntu
            logger.warning(e)
        self.__completer_model.setIconProvider(PathEditIconProvider())
        self.__completer_model.setRootPath(path)
        if file_filter:
            self.__completer_model.setFilter(file_filter)
        if name_filters:
            self.__completer_model.setNameFilters(name_filters)
        self.__completer.setModel(self.__completer_model)

        super(PathEdit, self).__init__(
            text=path,
            placeholder=placeholder,
            completer=self.__completer,
            edit_func=edit_func,
            save_func=save_func,
            horiz_policy=horiz_policy,
            parent=parent,
        )
        self.setObjectName(type(self).__name__)
        self.line_edit.setMinimumSize(QSize(250, 0))
        self.path_select = QPushButton(self)
        self.path_select.setObjectName(f"{type(self).__name__}Button")
        layout = self.layout()
        layout.addWidget(self.path_select)

        self.path_select.setText(self.tr("Browse..."))

        self.__file_mode = file_mode
        self.__file_filter = file_filter
        self.__name_filter = name_filters

        self.path_select.clicked.connect(self.__set_path)

    def setRootPath(self, path: str):
        self.__root_path = path
        self.__completer_model.setRootPath(path)

    def __set_path(self):
        dlg_path = self.line_edit.text()
        if not dlg_path or not os.path.isabs(dlg_path):
            dlg_path = self.__root_path
        dlg = QFileDialog(self, self.tr("Choose path"), dlg_path)
        dlg.setOption(QFileDialog.Option.DontUseCustomDirectoryIcons)
        dlg.setIconProvider(PathEditIconProvider())
        dlg.setFileMode(self.__file_mode)
        if self.__file_mode == QFileDialog.FileMode.Directory:
            dlg.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if self.__file_filter:
            dlg.setFilter(self.__file_filter)
        if self.__name_filter:
            dlg.setNameFilter(" ".join(self.__name_filter))
        if dlg.exec_():
            name = dlg.selectedFiles()[0]
            self.__completer_model.setRootPath(name)
            self.line_edit.setText(name)
