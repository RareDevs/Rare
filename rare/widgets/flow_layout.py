from typing import Optional, List, overload

from PyQt5.QtCore import Qt, QRect, QSize, QPoint
from PyQt5.QtWidgets import QLayout, QStyle, QSizePolicy, QLayoutItem, QWidget


class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super(FlowLayout, self).__init__(parent)
        self.setObjectName(type(self).__name__)
        self._hspacing = -1
        self._vspacing = -1
        self._items: List[QLayoutItem] = []

    def __del__(self):
        del self._items[:]

    @overload
    def indexOf(self, a0: QWidget) -> int:
        try:
            return next(idx for idx, item in enumerate(self._items) if item.widget() is a0)
        except:
            return -1

    def indexOf(self, a0: QLayoutItem) -> int:
        try:
            return self._items.index(a0)
        except:
            return -1

    def addItem(self, a0: QLayoutItem) -> None:
        self._items.append(a0)
        self.invalidate()

    def removeItem(self, a0: QLayoutItem) -> None:
        self._items.remove(a0)
        self.invalidate()

    def spacing(self) -> int:
        hspacing = self.horizontalSpacing()
        if hspacing == self.verticalSpacing():
            return hspacing
        else:
            return -1

    def setSpacing(self, a0: int) -> None:
        self._hspacing = self._vspacing = a0
        self.invalidate()

    def setHorizontalSpacing(self, a0: int) -> None:
        self._hspacing = a0
        self.invalidate()

    def horizontalSpacing(self):
        if self._hspacing >= 0:
            return self._hspacing
        else:
            return self.smartSpacing(QStyle.PM_LayoutHorizontalSpacing)

    def setVerticalSpacing(self, a0:  int) -> None:
        self._vspacing = a0
        self.invalidate()

    def verticalSpacing(self):
        if self._vspacing >= 0:
            return self._vspacing
        else:
            return self.smartSpacing(QStyle.PM_LayoutVerticalSpacing)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            self.invalidate()
            return item
        return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientations(Qt.Orientation(0))
        # return Qt.Horizontal | Qt.Vertical

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, a0: int) -> int:
        return self.doLayout(QRect(0, 0, a0, 0), True)

    def setGeometry(self, a0: QRect) -> None:
        super(FlowLayout, self).setGeometry(a0)
        self.doLayout(a0, False)

    def sizeHint(self) -> QSize:
        return QSize(
            self.parent().contentsRect().size().width(),
            self.minimumSize().height()
        )

    def minimumSize(self) -> QSize:
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
        if not self._items:
            return y + lineheight - rect.y() + bottom
        for item in self._items:
            if item.isEmpty():
                continue
            widget = item.widget()
            hspace = self.horizontalSpacing()
            if hspace == -1:
                hspace = widget.style().layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal
                )
            vspace = self.verticalSpacing()
            if vspace == -1:
                vspace = widget.style().layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical
                )
            nextX = x + item.sizeHint().width() + hspace
            if nextX - hspace > effective.right() and lineheight > 0:
                x = effective.x()
                y = y + lineheight + vspace
                nextX = x + item.sizeHint().width() + hspace
                lineheight = 0
            if not testonly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
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
