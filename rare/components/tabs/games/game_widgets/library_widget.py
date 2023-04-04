from typing import Optional, Tuple, List

from PyQt5.QtCore import Qt, QEvent, QObject
from PyQt5.QtGui import QPainter, QPixmap, QFontMetrics, QImage, QBrush, QColor, QShowEvent
from PyQt5.QtWidgets import QLabel

from rare.widgets.image_widget import ImageWidget


class ProgressLabel(QLabel):
    def __init__(self, parent=None):
        super(ProgressLabel, self).__init__(parent=parent)
        if self.parent() is not None:
            self.parent().installEventFilter(self)
        self.setObjectName(type(self).__name__)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFrameStyle(QLabel.StyledPanel)

    def __center_on_parent(self):
        fm = QFontMetrics(self.font())
        rect = fm.boundingRect(f"  {self.text()}  ")
        rect.moveCenter(self.parent().contentsRect().center())
        self.setGeometry(rect)

    def event(self, e: QEvent) -> bool:
        if e.type() == QEvent.ParentAboutToChange:
            if self.parent() is not None:
                self.parent().removeEventFilter(self)
        if e.type() == QEvent.ParentChange:
            if self.parent() is not None:
                self.parent().installEventFilter(self)
        return super().event(e)

    def showEvent(self, a0: QShowEvent) -> None:
        self.__center_on_parent()

    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        if a0 is self.parent() and a1.type() == QEvent.Resize:
            self.__center_on_parent()
            return a0.event(a1)
        return False

    @staticmethod
    def calculateColors(image: QImage) -> Tuple[QColor, QColor]:
        color: List[int] = [0, 0, 0]
        # take the two diagonals of the center square section
        min_d = min(image.width(), image.height())
        origin_w = (image.width() - min_d) // 2
        origin_h = (image.height() - min_d) // 2
        for x, y in zip(range(origin_w, min_d), range(origin_h, min_d)):
            pixel = image.pixelColor(x, y).getRgb()
            color = list(map(lambda t: sum(t) // 2, zip(pixel[0:3], color)))
        # take the V component of the HSV color
        fg_color = QColor(0, 0, 0) if QColor(*color).value() < 127 else QColor(255, 255, 255)
        bg_color = QColor(*map(lambda c: 255 - c, color))
        return bg_color, fg_color

    def setStyleSheetColors(self, bg: QColor, fg: QColor, brd: QColor):
        sheet = (
            f"QLabel#{type(self).__name__} {{"
            f"background-color: rgba({bg.red()}, {bg.green()}, {bg.blue()}, 65%);"
            f"color: rgb({fg.red()}, {fg.green()}, {fg.blue()});"
            f"border-color: rgb({brd.red()}, {brd.green()}, {brd.blue()});"
            f"}}"
        )
        self.setStyleSheet(sheet)


class LibraryWidget(ImageWidget):
    def __init__(self, parent=None) -> None:
        super(LibraryWidget, self).__init__(parent)
        self.progress_label = ProgressLabel(self)
        self.progress_label.setVisible(False)

        self._color_pixmap: Optional[QPixmap] = None
        self._gray_pixmap: Optional[QPixmap] = None
        # lk: keep percentage to not over-generate the image
        self._progress: int = -1

    def progressPixmap(self, color: QPixmap, gray: QPixmap, progress: int) -> QPixmap:
        """
        Paints the color image over the gray images based on progress percentage

        @param color:
        @param gray:
        @param progress:
        @return:
        """

        device = QPixmap(color.size())
        painter = QPainter(device)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, self._smooth_transform)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        # lk: Vertical loading
        # prog_h = (device.height() * progress // 100)
        # brush = QBrush(gray)
        # painter.fillRect(device.rect().adjusted(0, 0, 0, -prog_h), brush)
        # brush.setTexture(color)
        # painter.fillRect(device.rect().adjusted(0, device.height() - prog_h, 0, 0), brush)
        # lk: Horizontal loading
        prog_w = device.width() * progress // 100
        brush = QBrush(gray)
        painter.fillRect(device.rect().adjusted(prog_w, 0, 0, 0), brush)
        brush.setTexture(color)
        painter.fillRect(device.rect().adjusted(0, 0, prog_w - device.width(), 0), brush)
        painter.end()
        device.setDevicePixelRatio(color.devicePixelRatioF())
        return device

    def showProgress(self, color_pm: QPixmap, gray_pm: QPixmap) -> None:
        self._color_pixmap = color_pm
        self._gray_pixmap = gray_pm
        bg_color, fg_color = self.progress_label.calculateColors(color_pm.toImage())
        self.progress_label.setStyleSheetColors(bg_color, fg_color, fg_color)
        self.progress_label.setVisible(True)
        self.updateProgress(0)

    def updateProgress(self, progress: int):
        self.progress_label.setText(f"{progress:02}%")
        if progress > self._progress:
            self._progress = progress
            self.setPixmap(self.progressPixmap(self._color_pixmap, self._gray_pixmap, progress))

    def hideProgress(self, stopped: bool):
        self._color_pixmap = None
        self._gray_pixmap = None
        self.progress_label.setVisible(stopped)
        self._progress = -1
