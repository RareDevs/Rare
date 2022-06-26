from typing import Optional, Tuple, List

from PyQt5.QtCore import Qt, QRect, QEvent
from PyQt5.QtGui import QPainter, QPixmap, QResizeEvent, QFontMetrics, QImage, QBrush, QColor
from PyQt5.QtWidgets import QLabel

from rare.widgets.image_widget import ImageWidget


class ProgressLabel(QLabel):
    def __init__(self, parent):
        super(ProgressLabel, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFrameStyle(QLabel.StyledPanel)

    def setGeometry(self, a0: QRect) -> None:
        fm = QFontMetrics(self.font())
        rect = fm.boundingRect(f"  {self.text()}  ")
        rect.moveCenter(a0.center())
        super(ProgressLabel, self).setGeometry(rect)

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
            f"background-color: rgba({bg.red()}, {bg.green()}, {bg.blue()}, 65%);"
            f"color: rgb({fg.red()}, {fg.green()}, {fg.blue()});"
            f"border-width: 1px;"
            f"border-radius: 5%;"
            f"border-color: rgb({brd.red()}, {brd.green()}, {brd.blue()});"
            f"font-weight: bold;"
            f"font-size: 16pt;"
        )
        self.setStyleSheet(sheet)


class LibraryWidget(ImageWidget):
    _color_pixmap: Optional[QPixmap] = None
    _gray_pixmap: Optional[QPixmap] = None
    # lk: keep percentage to not over-generate the image
    _progress: int = -1

    def __init__(
        self,
        parent=None,
    ) -> None:
        super(LibraryWidget, self).__init__(parent)
        self.progress_label = ProgressLabel(self)
        self.progress_label.setVisible(False)

    def event(self, e: QEvent) -> bool:
        if e.type() == QEvent.LayoutRequest:
            self.progress_label.setGeometry(self.rect())
        return super(LibraryWidget, self).event(e)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        if self.progress_label.isVisible():
            self.progress_label.setGeometry(self.rect())
        super(LibraryWidget, self).resizeEvent(a0)

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
        self.progress_label.update()
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
