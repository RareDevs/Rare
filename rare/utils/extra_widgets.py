import io
import os
from logging import getLogger

from PIL import Image
from PyQt5.QtCore import Qt, QRect, QSize, QPoint, pyqtSignal, QUrl, QSettings
from PyQt5.QtGui import QMovie, QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QLayout, QStyle, QSizePolicy, QLabel, QFileDialog, QHBoxLayout, QWidget, QPushButton, \
    QStyleOptionTab, QStylePainter, QTabBar, QLineEdit, QToolButton
from qtawesome import icon

from rare import style_path
from rare.ui.utils.pathedit import Ui_PathEdit

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


class PathEdit(QWidget, Ui_PathEdit):
    def __init__(self,
                 text: str = "",
                 file_type: QFileDialog.FileType = QFileDialog.AnyFile,
                 type_filter: str = None,
                 name_filter: str = None,
                 edit_func: callable = None,
                 save_func: callable = None):
        super(PathEdit, self).__init__()
        self.setupUi(self)

        self.type_filter = type_filter
        self.name_filter = name_filter
        self.file_type = file_type
        self.edit_func = edit_func
        self.save_func = save_func
        if text:
            self.text_edit.setText(text)
        if self.edit_func is not None:
            self.text_edit.textChanged.connect(self.edit_func)
        if self.save_func is None:
            self.save_path_button.setVisible(False)
        else:
            self.text_edit.textChanged.connect(lambda t: self.save_path_button.setDisabled(False))
            self.save_path_button.clicked.connect(self.save)
            self.save_path_button.setDisabled(True)
        self.path_select.clicked.connect(self.set_path)

    def text(self):
        return self.text_edit.text()

    def setText(self, text: str):
        self.text_edit.setText(text)

    def save(self):
        self.save_func()
        self.save_path_button.setDisabled(True)

    def set_path(self):
        dlg_path = self.text_edit.text()
        if not dlg_path:
            dlg_path = os.path.expanduser("~/")
        dlg = QFileDialog(self, self.tr("Choose Path"), dlg_path)
        dlg.setFileMode(self.file_type)
        if self.type_filter:
            dlg.setFilter([self.type_filter])
        if self.name_filter:
            dlg.setNameFilter(self.name_filter)
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
        self.movie = QMovie(os.path.join(style_path, "loader.gif"))
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
            self.icon_view_button.setIcon(icon("mdi.view-grid-outline", color="orange"))
            self.list_view.setIcon(icon("fa5s.list", color="white"))
        else:
            self.icon_view_button.setIcon(icon("mdi.view-grid-outline", color="white"))
            self.list_view.setIcon(icon("fa5s.list", color="orange"))

        self.icon_view_button.clicked.connect(self.icon)
        self.list_view.clicked.connect(self.list)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.icon_view_button)
        self.layout.addWidget(self.list_view)

        self.setLayout(self.layout)

    def isChecked(self):
        return self.icon_view

    def icon(self):
        self.icon_view_button.setIcon(icon("mdi.view-grid-outline", color="orange"))
        self.list_view.setIcon(icon("fa5s.list", color="white"))
        self.icon_view = False
        self.toggled.emit()

    def list(self):
        self.icon_view_button.setIcon(icon("mdi.view-grid-outline", color="white"))
        self.list_view.setIcon(icon("fa5s.list", color="orange"))
        self.icon_view = True
        self.toggled.emit()


class ImageLabel(QLabel):

    def __init__(self):
        super(ImageLabel, self).__init__()
        path = os.path.expanduser("~/.cache/rare/cache")
        if p := os.environ.get("XDG_CACHE_HOME"):
            path = os.path.join(p, "rare", "cache")
        self.path = path
        self.manager = QNetworkAccessManager()

    def update_image(self, url, name, size: tuple = (240, 320)):
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
            self.request = self.manager.get(QNetworkRequest(QUrl(url)))
            self.request.finished.connect(self.image_ready)
        else:
            self.show_image()

    def image_ready(self):
        self.setPixmap(QPixmap())
        if self.request:
            if self.request.error() == QNetworkReply.NoError:
                data = self.request.readAll().data()
                image: Image.Image = Image.open(io.BytesIO(data))
                image = image.resize((self.img_size[0], self.img_size[1]))

                if QSettings().value("cache_images", True, bool):
                    image.save(os.path.join(self.path, self.name), format="png")
                byte_array = io.BytesIO()
                image.save(byte_array, format="PNG")
                # pixmap = QPixmap.fromImage(ImageQt(image))
                pixmap = QPixmap()
                pixmap.loadFromData(byte_array.getvalue())
                # pixmap = QPixmap.fromImage(ImageQt.ImageQt(image))
                self.setPixmap(pixmap)
            else:
                logger.error(self.request.errorString())
        else:
            return

    def show_image(self):
        self.image = QPixmap(os.path.join(self.path, self.name)).scaled(*self.img_size,
                                                                        transformMode=Qt.SmoothTransformation)
        self.setPixmap(self.image)


class ButtonLineEdit(QLineEdit):
    buttonClicked = pyqtSignal()

    def __init__(self, icon_name, placeholder_text: str, parent=None):
        super(ButtonLineEdit, self).__init__(parent)

        self.button = QToolButton(self)
        self.button.setIcon(icon(icon_name, color="white"))
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
                         (self.rect().bottom() - buttonSize.height() + 1) / 2)
        super(ButtonLineEdit, self).resizeEvent(event)
