import os
from logging import getLogger
from typing import Callable, Tuple

from PyQt5.QtCore import Qt, QCoreApplication, QRect, QSize, QPoint, pyqtSignal, QFileInfo
from PyQt5.QtGui import QMovie, QPixmap, QFontMetrics, QImage
from PyQt5.QtWidgets import QLayout, QStyle, QSizePolicy, QLabel, QFileDialog, QHBoxLayout, QWidget, QPushButton, \
    QStyleOptionTab, QStylePainter, QTabBar, QLineEdit, QToolButton, QTabWidget, QCompleter, QFileSystemModel, \
    QStyledItemDelegate, QFileIconProvider
from qtawesome import icon as qta_icon

from rare import cache_dir
from rare.utils.qt_requests import QtRequestManager

logger = getLogger("ExtraWidgets")


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=-1, hspacing=-1, vspacing=-1):
        super(FlowLayout, self).__init__(parent)
        self._hspacing = hspacing
        self._vspacing = vspacing
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        del self._items[:]

    def addItem(self, item):
        self._items.append(item)

    def horizontalSpacing(self):
        if self._hspacing >= 0:
            return self._hspacing
        else:
            return self.smartSpacing(
                QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self):
        if self._vspacing >= 0:
            return self._vspacing
        else:
            return self.smartSpacing(
                QStyle.PM_LayoutVerticalSpacing)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)
        return size

    def doLayout(self, rect, testonly):
        left, top, right, bottom = self.getContentsMargins()
        effective = rect.adjusted(+left, +top, -right, -bottom)
        x = effective.x()
        y = effective.y()
        lineheight = 0
        for item in self._items:
            widget = item.widget()
            if not widget.isVisible():
                continue
            hspace = self.horizontalSpacing()
            if hspace == -1:
                hspace = widget.style().layoutSpacing(
                    QSizePolicy.PushButton,
                    QSizePolicy.PushButton, Qt.Horizontal)
            vspace = self.verticalSpacing()
            if vspace == -1:
                vspace = widget.style().layoutSpacing(
                    QSizePolicy.PushButton,
                    QSizePolicy.PushButton, Qt.Vertical)
            nextX = x + item.sizeHint().width() + hspace
            if nextX - hspace > effective.right() and lineheight > 0:
                x = effective.x()
                y = y + lineheight + vspace
                nextX = x + item.sizeHint().width() + hspace
                lineheight = 0
            if not testonly:
                item.setGeometry(
                    QRect(QPoint(x, y), item.sizeHint()))
            x = nextX
            lineheight = max(lineheight, item.sizeHint().height())
        return y + lineheight - rect.y() + bottom

    def smartSpacing(self, pm):
        parent = self.parent()
        if parent is None:
            return -1
        elif parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()


class IndicatorLineEdit(QWidget):
    textChanged = pyqtSignal(str)
    is_valid = False

    def __init__(self,
                 text: str = "",
                 ph_text: str = "",
                 completer: QCompleter = None,
                 edit_func: Callable[[str], Tuple[bool, str]] = None,
                 save_func: Callable[[str], None] = None,
                 horiz_policy: QSizePolicy = QSizePolicy.Expanding,
                 parent=None):
        super(IndicatorLineEdit, self).__init__(parent=parent)
        self.setObjectName("IndicatorLineEdit")
        self.layout = QHBoxLayout(self)
        self.layout.setObjectName("layout")
        self.layout.setContentsMargins(0, 0, 0, 0)
        # Add line_edit
        self.line_edit = QLineEdit(self)
        self.line_edit.setObjectName("line_edit")
        self.line_edit.setPlaceholderText(ph_text)
        self.line_edit.setSizePolicy(horiz_policy, QSizePolicy.Fixed)
        # Add hint_label to line_edit
        self.line_edit.setLayout(QHBoxLayout())
        self.hint_label = QLabel()
        self.hint_label.setObjectName('HintLabel')
        self.hint_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.line_edit.layout().setContentsMargins(0, 0, 10, 0)
        self.line_edit.layout().addWidget(self.hint_label)
        # Add completer
        if completer is not None:
            completer.popup().setItemDelegate(QStyledItemDelegate(self))
            completer.popup().setAlternatingRowColors(True)
            self.line_edit.setCompleter(completer)
        self.layout.addWidget(self.line_edit)
        if edit_func is not None:
            self.indicator_label = QLabel()
            self.indicator_label.setPixmap(qta_icon("ei.info-circle", color="gray").pixmap(16, 16))
            self.indicator_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.layout.addWidget(self.indicator_label)

        if not ph_text:
            _translate = QCoreApplication.translate
            self.line_edit.setPlaceholderText(_translate(self.__class__.__name__, "Default"))

        self.edit_func = edit_func
        self.save_func = save_func
        self.line_edit.textChanged.connect(self.__edit)
        if self.edit_func is None:
            self.line_edit.textChanged.connect(self.__save)

        # lk: this can be placed here to trigger __edit
        # lk: it going to save the input again if it is valid which
        # lk: is ok to do given the checks don't misbehave (they shouldn't)
        # lk: however it is going to edit any "understood" bad input to good input
        # lk: and we might not want that (but the validity check reports on the edited string)
        # lk: it is also going to trigger this widget's textChanged signal but that gets lost
        if text:
            self.line_edit.setText(text)

    def text(self) -> str:
        return self.line_edit.text()

    def setText(self, text: str):
        self.line_edit.setText(text)

    def setHintText(self, text: str):
        self.hint_label.setFrameRect(self.line_edit.rect())
        self.hint_label.setText(text)

    def __indicator(self, res):
        color = "green" if res else "red"
        self.indicator_label.setPixmap(qta_icon("ei.info-circle", color=color).pixmap(16, 16))

    def __edit(self, text):
        if self.edit_func is not None:
            self.line_edit.blockSignals(True)
            self.is_valid, text = self.edit_func(text)
            if text != self.line_edit.text():
                self.line_edit.setText(text)
            self.line_edit.blockSignals(False)
            self.__indicator(self.is_valid)
            if self.is_valid:
                self.__save(text)
            self.textChanged.emit(text)

    def __save(self, text):
        if self.save_func is not None:
            self.save_func(text)


class PathEditIconProvider(QFileIconProvider):
    icons = [
        'mdi.file-cancel',      # Unknown
        'mdi.desktop-classic',  # Computer
        'mdi.desktop-mac',      # Desktop
        'mdi.trash-can',        # Trashcan
        'mdi.server-network',   # Network
        'mdi.harddisk',         # Drive
        'mdi.folder',           # Folder
        'mdi.file',             # File
        'mdi.cog',              # Executable
    ]

    def __init__(self):
        super(PathEditIconProvider, self).__init__()
        self.icon_types = dict()
        for idx, icn in enumerate(self.icons):
            self.icon_types.update({idx-1: qta_icon(icn, color='#eeeeee')})

    def icon(self, info_type):
        if isinstance(info_type, QFileInfo):
            if info_type.isRoot():
                return self.icon_types[4]
            if info_type.isDir():
                return self.icon_types[5]
            if info_type.isFile():
                return self.icon_types[6]
            if info_type.isExecutable():
                return self.icon_types[7]
            return self.icon_types[-1]
        return self.icon_types[int(info_type)]


class PathEdit(IndicatorLineEdit):
    completer = QCompleter()
    compl_model = QFileSystemModel()

    def __init__(self,
                 path: str = "",
                 file_type: QFileDialog.FileType = QFileDialog.AnyFile,
                 type_filter: str = "",
                 name_filter: str = "",
                 ph_text: str = "",
                 edit_func: Callable[[str], Tuple[bool, str]] = None,
                 save_func: Callable[[str], None] = None,
                 horiz_policy: QSizePolicy = QSizePolicy.Expanding,
                 parent=None):
        self.compl_model.setOptions(QFileSystemModel.DontWatchForChanges |
                                    QFileSystemModel.DontResolveSymlinks |
                                    QFileSystemModel.DontUseCustomDirectoryIcons)
        self.compl_model.setIconProvider(PathEditIconProvider())
        self.compl_model.setRootPath(path)
        self.completer.setModel(self.compl_model)
        super(PathEdit, self).__init__(text=path, ph_text=ph_text, completer=self.completer,
                                       edit_func=edit_func, save_func=save_func,
                                       horiz_policy=horiz_policy, parent=parent)
        self.setObjectName("PathEdit")
        self.line_edit.setMinimumSize(QSize(300, 0))
        self.path_select = QToolButton(self)
        self.path_select.setObjectName("path_select")
        self.layout.addWidget(self.path_select)

        _translate = QCoreApplication.translate
        self.path_select.setText(_translate("PathEdit", "Browse..."))

        self.type_filter = type_filter
        self.name_filter = name_filter
        self.file_type = file_type

        self.path_select.clicked.connect(self.__set_path)

    def __set_path(self):
        dlg_path = self.line_edit.text()
        if not dlg_path:
            dlg_path = os.path.expanduser("~/")
        dlg = QFileDialog(self, self.tr("Choose path"), dlg_path)
        dlg.setFileMode(self.file_type)
        if self.type_filter:
            dlg.setFilter([self.type_filter])
        if self.name_filter:
            dlg.setNameFilter(self.name_filter)
        if dlg.exec_():
            names = dlg.selectedFiles()
            self.line_edit.setText(names[0])
            self.compl_model.setRootPath(names[0])


class SideTabBar(QTabBar):
    def __init__(self, parent=None):
        super(SideTabBar, self).__init__(parent=parent)
        self.setObjectName("SideTabBar")
        self.fm = QFontMetrics(self.font())

    def tabSizeHint(self, index):
        # width = QTabBar.tabSizeHint(self, index).width()
        return QSize(200, self.fm.height() + 18)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QRect(QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QStyle.CE_TabBarTabLabel, opt)
            painter.restore()


class SideTabWidget(QTabWidget):
    back_clicked = pyqtSignal()

    def __init__(self, show_back: bool = False, parent=None):
        super(SideTabWidget, self).__init__(parent=parent)
        self.setTabBar(SideTabBar())
        self.setDocumentMode(True)
        self.setTabPosition(QTabWidget.West)
        if show_back:
            self.addTab(QWidget(), qta_icon("mdi.keyboard-backspace"), self.tr("Back"))
            self.tabBarClicked.connect(self.back_func)

    def back_func(self, tab):
        # shortcut for tab == 0
        if not tab:
            self.back_clicked.emit()


class WaitingSpinner(QLabel):
    def __init__(self):
        super(WaitingSpinner, self).__init__()
        self.setStyleSheet("""
            margin-left: auto;
            margin-right: auto;
        """)
        self.movie = QMovie(":/images/loader.gif")
        self.setMovie(self.movie)
        self.movie.start()


class SelectViewWidget(QWidget):
    toggled = pyqtSignal()

    def __init__(self, icon_view: bool):
        super(SelectViewWidget, self).__init__()
        self.icon_view = icon_view
        self.setStyleSheet("""QPushButton{border: none; background-color: transparent}""")
        self.icon_view_button = QPushButton()
        self.list_view = QPushButton()
        if icon_view:
            self.icon_view_button.setIcon(qta_icon("mdi.view-grid-outline", color="orange"))
            self.list_view.setIcon(qta_icon("fa5s.list"))
        else:
            self.icon_view_button.setIcon(qta_icon("mdi.view-grid-outline"))
            self.list_view.setIcon(qta_icon("fa5s.list", color="orange"))

        self.icon_view_button.clicked.connect(self.icon)
        self.list_view.clicked.connect(self.list)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.icon_view_button)
        self.layout.addWidget(self.list_view)

        self.setLayout(self.layout)

    def isChecked(self):
        return self.icon_view

    def icon(self):
        self.icon_view_button.setIcon(qta_icon("mdi.view-grid-outline", color="orange"))
        self.list_view.setIcon(qta_icon("fa5s.list"))
        self.icon_view = False
        self.toggled.emit()

    def list(self):
        self.icon_view_button.setIcon(qta_icon("mdi.view-grid-outline"))
        self.list_view.setIcon(qta_icon("fa5s.list", color="orange"))
        self.icon_view = True
        self.toggled.emit()


class ImageLabel(QLabel):
    image = None
    img_size = None
    name = str()

    def __init__(self):
        super(ImageLabel, self).__init__()
        self.path = cache_dir
        self.manager = QtRequestManager("bytes")

    def update_image(self, url, name="", size: tuple = (240, 320)):
        self.setFixedSize(*size)
        self.img_size = size
        self.name = name
        for c in r'<>?":|\/* ':
            self.name = self.name.replace(c, "")
        if self.img_size[0] > self.img_size[1]:
            name_extension = "wide"
        else:
            name_extension = "tall"
        self.name = f"{self.name}_{name_extension}.png"
        if not os.path.exists(os.path.join(self.path, self.name)):
            self.manager.get(url, self.image_ready)
            # self.request.finished.connect(self.image_ready)
        else:
            self.show_image()

    def image_ready(self, data):
        try:
            self.setPixmap(QPixmap())
        except Exception:
            logger.warning("C++ object already removed, when image ready")
            return
        image = QImage()
        image.loadFromData(data)
        image = image.scaled(*self.img_size[:2], Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)

        pixmap = QPixmap().fromImage(image)
        self.setPixmap(pixmap)

    def show_image(self):
        self.image = QPixmap(os.path.join(self.path, self.name)).scaled(*self.img_size,
                                                                        transformMode=Qt.SmoothTransformation)
        self.setPixmap(self.image)


class ButtonLineEdit(QLineEdit):
    buttonClicked = pyqtSignal()

    def __init__(self, icon_name, placeholder_text: str, parent=None):
        super(ButtonLineEdit, self).__init__(parent)

        self.button = QToolButton(self)
        self.button.setIcon(qta_icon(icon_name, color="white"))
        self.button.setStyleSheet('border: 0px; padding: 0px;')
        self.button.setCursor(Qt.ArrowCursor)
        self.button.clicked.connect(self.buttonClicked.emit)
        self.setPlaceholderText(placeholder_text)
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        buttonSize = self.button.sizeHint()

        self.setStyleSheet('QLineEdit {padding-right: %dpx; }' % (buttonSize.width() + frameWidth + 1))
        self.setMinimumSize(max(self.minimumSizeHint().width(), buttonSize.width() + frameWidth * 2 + 2),
                            max(self.minimumSizeHint().height(), buttonSize.height() + frameWidth * 2 + 2))

    def resizeEvent(self, event):
        buttonSize = self.button.sizeHint()
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.button.move(self.rect().right() - frameWidth - buttonSize.width(),
                         (self.rect().bottom() - buttonSize.height() + 1) // 2)
        super(ButtonLineEdit, self).resizeEvent(event)
