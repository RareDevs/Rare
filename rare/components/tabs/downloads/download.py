from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import (
    QPixmap,
    QImage,
    QPainter,
    QBrush,
    QLinearGradient,
    QPaintEvent,
    QPalette,
)

from rare.ui.components.tabs.downloads.download_widget import Ui_DownloadWidget
from rare.widgets.image_widget import ImageWidget


class DownloadWidget(ImageWidget):
    def __init__(self, parent=None):
        super(DownloadWidget, self).__init__(parent=parent)
        self.ui = Ui_DownloadWidget()
        self.ui.setupUi(self)

    """
    Painting overrides
    Let them live here until a better alternative is divised.

    This is also part of list_game_widget and maybe a
    common base can bring them together.
    """

    def prepare_pixmap(self, pixmap: QPixmap) -> QPixmap:
        device: QImage = QImage(
            pixmap.size().width() * 3,
            int(self.sizeHint().height() * pixmap.devicePixelRatioF()) + 1,
            QImage.Format_ARGB32_Premultiplied,
        )
        painter = QPainter(device)
        brush = QBrush(pixmap)
        painter.fillRect(device.rect(), brush)
        # the gradient could be cached and reused as it is expensive
        gradient = QLinearGradient(0, 0, device.width(), 0)
        gradient.setColorAt(0.15, Qt.transparent)
        gradient.setColorAt(0.5, Qt.black)
        gradient.setColorAt(0.85, Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.fillRect(device.rect(), gradient)
        painter.end()
        ret = QPixmap.fromImage(device)
        ret.setDevicePixelRatio(pixmap.devicePixelRatioF())
        return ret

    def setPixmap(self, pixmap: QPixmap) -> None:
        # lk: trade some possible delay and start-up time
        # lk: for faster rendering. Gradients are expensive
        # lk: so pre-generate the image
        super(DownloadWidget, self).setPixmap(self.prepare_pixmap(pixmap))

    def paint_image_empty(self, painter: QPainter, a0: QPaintEvent) -> None:
        # when pixmap object is not available yet, show a gray rectangle
        painter.setOpacity(0.5 * self._opacity)
        painter.fillRect(a0.rect(), self.palette().color(QPalette.Background))

    def paint_image_cover(self, painter: QPainter, a0: QPaintEvent) -> None:
        painter.setOpacity(self._opacity)
        color = self.palette().color(QPalette.Background).darker(75)
        painter.fillRect(self.rect(), color)
        brush = QBrush(self._pixmap)
        brush.setTransform(self._transform)
        width = int(self._pixmap.width() / self._pixmap.devicePixelRatioF())
        origin = self.width() - width
        painter.setBrushOrigin(origin, 0)
        fill_rect = QRect(origin, 0, width, self.height())
        painter.fillRect(fill_rect, brush)
