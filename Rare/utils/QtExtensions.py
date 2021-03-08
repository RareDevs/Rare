import os

from PyQt5.QtCore import Qt, QRect, QSize, QPoint, pyqtSignal, QPropertyAnimation, pyqtSlot, QPointF, QEasingCurve, \
    QObject, pyqtProperty
from PyQt5.QtGui import QMovie, QPainter, QPalette, QLinearGradient, QGradient
from PyQt5.QtWidgets import QLayout, QStyle, QSizePolicy, QLabel, QFileDialog, QHBoxLayout, QWidget, QLineEdit, \
    QPushButton, QStyleOptionTab, QStylePainter, QTabBar, QAbstractButton, QCheckBox

from Rare import style_path


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


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self):
        super(ClickableLabel, self).__init__()


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
            dlg.setFilter([self.filter])
        if dlg.exec_():
            names = dlg.selectedFiles()
            self.text_edit.setText(names[0])


class SideTabBar(QTabBar):
    def __init__(self):
        super(SideTabBar, self).__init__()
        self.setObjectName("settings_bar")

    def tabSizeHint(self, index):
        # width = QTabBar.tabSizeHint(self, index).width()
        return QSize(200, 30)

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
            painter.drawControl(QStyle.CE_TabBarTabLabel, opt);
            painter.restore()

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


class SwitchPrivate(QObject):
    def __init__(self, q, parent=None):
        QObject.__init__(self, parent=parent)
        self.mPointer = q
        self.mPosition = 0.0
        self.mGradient = QLinearGradient()
        self.mGradient.setSpread(QGradient.PadSpread)

        self.animation = QPropertyAnimation(self)
        self.animation.setTargetObject(self)
        self.animation.setPropertyName(b'position')
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutExpo)

        self.animation.finished.connect(self.mPointer.update)

    @pyqtProperty(float)
    def position(self):
        return self.mPosition

    @position.setter
    def position(self, value):
        self.mPosition = value
        self.mPointer.update()

    def draw(self, painter):
        r = self.mPointer.rect()
        margin = r.height()/10
        shadow = self.mPointer.palette().color(QPalette.Dark)
        light = self.mPointer.palette().color(QPalette.Light)
        button = self.mPointer.palette().color(QPalette.Button)
        painter.setPen(Qt.NoPen)

        self.mGradient.setColorAt(0, shadow.darker(130))
        self.mGradient.setColorAt(1, light.darker(130))
        self.mGradient.setStart(0, r.height())
        self.mGradient.setFinalStop(0, 0)
        painter.setBrush(self.mGradient)
        painter.drawRoundedRect(r, r.height()/2, r.height()/2)

        self.mGradient.setColorAt(0, shadow.darker(140))
        self.mGradient.setColorAt(1, light.darker(160))
        self.mGradient.setStart(0, 0)
        self.mGradient.setFinalStop(0, r.height())
        painter.setBrush(self.mGradient)
        painter.drawRoundedRect(r.adjusted(margin, margin, -margin, -margin), r.height()/2, r.height()/2)

        self.mGradient.setColorAt(0, button.darker(130))
        self.mGradient.setColorAt(1, button)

        painter.setBrush(self.mGradient)

        x = r.height()/2.0 + self.mPosition*(r.width()-r.height())
        painter.drawEllipse(QPointF(x, r.height()/2), r.height()/2-margin, r.height()/2-margin)

    @pyqtSlot(bool, name='animate')
    def animate(self, checked):
        self.animation.setDirection(QPropertyAnimation.Forward if checked else QPropertyAnimation.Backward)
        self.animation.start()


class Switch(QAbstractButton):
    def __init__(self):
        QAbstractButton.__init__(self)
        self.dPtr = SwitchPrivate(self)
        self.setCheckable(True)
        self.clicked.connect(self.dPtr.animate)

    def sizeHint(self):
        return QSize(42, 21)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.dPtr.draw(painter)

    def setChecked(self, a0: bool) -> None:
        super().setChecked(a0)
        self.dPtr.animate(a0)

    def resizeEvent(self, event):
        self.update()
