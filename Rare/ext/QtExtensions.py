import os

from PyQt5.QtCore import Qt, QRect, QPoint, QSize
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import *

from Rare import style_path


class CustomQLabel(QLabel):
    def __init__(self, *__args):
        super().__init__(*__args)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)


class WaitingSpinner(QLabel):
    def __init__(self):
        super(WaitingSpinner, self).__init__()
        self.setStyleSheet("""
            margin-left: auto;
            margin-right: auto;
        """)
        self.movie = QMovie(style_path+"Icons/loader.gif")
        self.setMovie(self.movie)
        self.movie.start()


class PathEdit(QWidget):
    def __init__(self, text: str = "", type_of_file: QFileDialog.FileType = QFileDialog.AnyFile, infotext: str = "",
                 filter: str = None):
        super(PathEdit, self).__init__()
        self.filter = filter
        self.type_of_file = type_of_file
        self.info_text = infotext
        self.layout = QHBoxLayout()
        self.text_edit = QLineEdit(text)
        self.path_select = QPushButton(self.tr("Select Path"))
        self.path_select.clicked.connect(self.set_path)
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.path_select)
        self.setLayout(self.layout)

    def setPlaceholderText(self, text: str):
        self.text_edit.setPlaceholderText(text)

    def text(self):
        return self.text_edit.text()

    def set_path(self):
        dlg = QFileDialog(self, self.tr("Choose Path"), os.path.expanduser("~/"))
        dlg.setFileMode(self.type_of_file)
        if self.filter:
            dlg.setFilter(self.filter)
        if dlg.exec_():
            names = dlg.selectedFiles()
            self.text_edit.setText(names[0])



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