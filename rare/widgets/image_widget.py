from enum import Enum
from typing import Tuple, Optional, Union

from PyQt5.QtCore import Qt, QRectF, QSize
from PyQt5.QtGui import (
    QPaintEvent,
    QPainter,
    QPixmap,
    QTransform,
    QBrush,
    QPalette,
    QPainterPath,
    QLinearGradient,
    QColor,
)
from PyQt5.QtWidgets import QWidget

from rare.models.image import ImageSize

OverlayPath = Tuple[QPainterPath, Union[QColor, QLinearGradient]]


class ImageWidget(QWidget):
    class Border(Enum):
        Rounded = 0
        Squared = 1

    _pixmap: Optional[QPixmap] = None
    _opacity: float = 1.0
    _transform: QTransform
    _smooth_transform: bool = False
    _rounded_overlay: Optional[OverlayPath] = None
    _squared_overlay: Optional[OverlayPath] = None
    _image_size: Optional[ImageSize.Preset] = None

    def __init__(self, parent=None) -> None:
        super(ImageWidget, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setContentsMargins(0, 0, 0, 0)
        self.paint_image = self.paint_image_empty
        self.paint_overlay = self.paint_overlay_rounded

    def setOpacity(self, value: float) -> None:
        self._opacity = value
        self.update()

    def setPixmap(self, pixmap: QPixmap) -> None:
        if not pixmap.isNull():
            self._pixmap = pixmap
            self.paint_image = self.paint_image_cover
            if not self._image_size:
                self._transform = QTransform().scale(
                    1 / pixmap.devicePixelRatioF(),
                    1 / pixmap.devicePixelRatioF(),
                )
            else:
                self._transform = QTransform().scale(
                    1 / pixmap.devicePixelRatioF() / self._image_size.divisor,
                    1 / pixmap.devicePixelRatioF() / self._image_size.divisor,
                )
        else:
            self.paint_image = self.paint_image_empty
        self.update()

    def sizeHint(self) -> QSize:
        return self._image_size.size if self._image_size else super(ImageWidget, self).sizeHint()

    def minimumSizeHint(self) -> QSize:
        return self._image_size.size if self._image_size else super(ImageWidget, self).minimumSizeHint()

    def setFixedSize(self, a0: ImageSize.Preset) -> None:
        self._squared_overlay = None
        self._rounded_overlay = None
        self._image_size = a0
        self._smooth_transform = a0.smooth
        super(ImageWidget, self).setFixedSize(a0.size)

    def setBorder(self, border: Border):
        if border == ImageWidget.Border.Rounded:
            self.paint_overlay = self.paint_overlay_rounded
        else:
            self.paint_overlay = self.paint_overlay_squared
        self.update()

    def _generate_squared_overlay(self) -> OverlayPath:
        if self._image_size is not None and self._squared_overlay is not None:
            return self._squared_overlay
        path = QPainterPath()
        path.addRect(0, 0, self.width(), self.height())
        border = 2
        inner_path = QPainterPath()
        inner_path.addRect(
            QRectF(
                border,
                border,
                self.width() - border * 2,
                self.height() - border * 2,
            )
        )
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, Qt.black)
        gradient.setColorAt(1.0, Qt.transparent)
        self._squared_overlay = path.subtracted(inner_path), gradient
        return self._squared_overlay

    def _generate_rounded_overlay(self) -> OverlayPath:
        if self._image_size is not None and self._rounded_overlay is not None:
            return self._rounded_overlay
        # lk: the '-1' and '+1' are adjustments required for anti-aliasing
        # lk: otherwise vertical lines would appear at the edges
        path = QPainterPath()
        path.addRect(-1, -1, self.width() + 2, self.height() + 2)
        rounded_path = QPainterPath()
        rounded_path.addRoundedRect(
            QRectF(0, 0, self.width(), self.height()),
            self.height() * 0.045,
            self.height() * 0.045,
        )
        self._rounded_overlay = path.subtracted(rounded_path), QColor(0, 0, 0, 0)
        return self._rounded_overlay

    def paint_image_empty(self, painter: QPainter, a0: QPaintEvent) -> None:
        # when pixmap object is not available yet, show a gray rectangle
        painter.setOpacity(0.5 * self._opacity)
        painter.fillRect(a0.rect(), Qt.darkGray)

    def paint_image_cover(self, painter: QPainter, a0: QPaintEvent) -> None:
        painter.setOpacity(self._opacity)
        brush = QBrush(self._pixmap)
        # downscale the image during painting to fit the pixelratio
        brush.setTransform(self._transform)
        painter.fillRect(a0.rect(), brush)

    def paint_overlay_rounded(self, painter: QPainter, a0: QPaintEvent) -> None:
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setOpacity(1.0)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        overlay, _ = self._generate_rounded_overlay()
        painter.fillPath(overlay, self.palette().color(QPalette.Background))

    def paint_overlay_squared(self, painter: QPainter, a0: QPaintEvent) -> None:
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setOpacity(self._opacity)
        painter.fillPath(*self._generate_squared_overlay())

    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter(self)
        if not painter.paintEngine().isActive():
            return
        # helps with better image quality
        painter.setRenderHint(QPainter.SmoothPixmapTransform, self._smooth_transform)
        self.paint_image(painter, a0)
        self.paint_overlay(painter, a0)
        painter.end()


__all__ = ["ImageSize", "ImageWidget"]

