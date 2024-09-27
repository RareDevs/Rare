from logging import getLogger

from PySide6.QtCore import Qt, QEvent, QRect, Slot
from PySide6.QtGui import (
    QPalette,
    QBrush,
    QPaintEvent,
    QPainter,
    QLinearGradient,
    QPixmap,
    QImage,
)

from rare.models.game import RareGame
from rare.models.image import ImageSize
from rare.utils.misc import format_size
from .game_widget import GameWidget
from .list_widget import ListWidget

logger = getLogger("ListGameWidget")


class ListGameWidget(GameWidget):
    def __init__(self, rgame: RareGame, parent=None):
        super().__init__(rgame, parent)
        self.setObjectName(f"{rgame.app_name}")
        self.ui = ListWidget()
        self.ui.setupUi(self)

        self.ui.title_label.setText(self.rgame.app_title)
        self.ui.launch_btn.clicked.connect(self._launch)
        self.ui.launch_btn.setVisible(self.rgame.is_installed)
        self.ui.install_btn.clicked.connect(self._install)
        self.ui.install_btn.setVisible(not self.rgame.is_installed)

        self.ui.launch_btn.setEnabled(self.rgame.can_launch)

        self.ui.launch_btn.setText(
            self.tr("Launch") if not self.rgame.is_origin else self.tr("Link/Play")
        )
        self.ui.developer_label.setText(self.rgame.developer)
        # self.version_label.setVisible(self.is_installed)
        if self.rgame.igame:
            self.ui.version_label.setText(self.rgame.version)
        self.ui.size_label.setText(format_size(self.rgame.install_size) if self.rgame.install_size else "")

        self.update_state()

        # lk: "connect" the buttons' enter/leave events to this widget
        self.installEventFilter(self)
        self.ui.launch_btn.installEventFilter(self)
        self.ui.install_btn.installEventFilter(self)

    @Slot()
    def update_pixmap(self):
        self.setPixmap(self.rgame.get_pixmap(ImageSize.LibraryWide, self.rgame.is_installed))

    @Slot()
    def start_progress(self):
        self.showProgress(
            self.rgame.get_pixmap(ImageSize.LibraryWide, True),
            self.rgame.get_pixmap(ImageSize.LibraryWide, False)
        )

    def enterEvent(self, a0: QEvent = None) -> None:
        if a0 is not None:
            a0.accept()
        self.ui.tooltip_label.setVisible(True)

    def leaveEvent(self, a0: QEvent = None) -> None:
        if a0 is not None:
            a0.accept()
        self.ui.tooltip_label.setVisible(False)

    """
    Painting and progress overrides.
    Let them live here until a better alternative is divised.
    
    The list widget and these painting functions can be
    refactored to be used in downloads and/or dlcs
    """

    def prepare_pixmap(self, pixmap: QPixmap) -> QPixmap:
        device: QImage = QImage(
            pixmap.size().width() * 1,
            int(self.sizeHint().height() * pixmap.devicePixelRatioF()) + 1,
            QImage.Format.Format_ARGB32_Premultiplied
        )
        painter = QPainter(device)
        pixmap = pixmap.copy(
            0, (pixmap.height() - self.sizeHint().height()) // 2,
            pixmap.width(), self.sizeHint().height()
        )
        brush = QBrush(pixmap)
        painter.fillRect(device.rect(), brush)
        # the gradient could be cached and reused as it is expensive
        gradient = QLinearGradient(0, 0, device.width(), 0)
        gradient.setColorAt(0.02, Qt.GlobalColor.transparent)
        gradient.setColorAt(0.5, Qt.GlobalColor.black)
        gradient.setColorAt(0.98, Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        painter.fillRect(device.rect(), gradient)
        painter.end()
        ret = QPixmap.fromImage(device)
        ret.setDevicePixelRatio(pixmap.devicePixelRatioF())
        return ret

    def setPixmap(self, pixmap: QPixmap) -> None:
        # lk: trade some possible delay and start-up time
        # lk: for faster rendering. Gradients are expensive
        # lk: so pre-generate the image
        if not pixmap.isNull():
            pixmap = self.prepare_pixmap(pixmap)
        super(ListGameWidget, self).setPixmap(pixmap)

    def paint_image_cover(self, painter: QPainter, a0: QPaintEvent) -> None:
        painter.setOpacity(self._opacity)
        color = self.palette().color(QPalette.ColorRole.Window).darker(75)
        painter.fillRect(self.rect(), color)
        brush = QBrush(self._pixmap)
        brush.setTransform(self._transform)
        width = int(self._pixmap.width() / self._pixmap.devicePixelRatioF())
        origin = self.width() // 2
        painter.setBrushOrigin(origin, 0)
        fill_rect = QRect(origin, 0, width, self.height())
        painter.fillRect(fill_rect, brush)

    def progressPixmap(self, color: QPixmap, gray: QPixmap, progress: int) -> QPixmap:
        # lk: so about that +1 after the in convertion, casting to int rounds down
        # lk: and that can create a weird line at the bottom, add 1 to round up.
        device = QPixmap(
            color.size().width(),
            int(self.sizeHint().height() * color.devicePixelRatioF()) + 1,
        )
        painter = QPainter(device)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, self._smooth_transform)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        prog_h = (device.height() * progress // 100)
        gray = gray.copy(
            0, (gray.height() - self.sizeHint().height()) // 2,
            gray.width(), self.sizeHint().height()
        )
        brush = QBrush(gray)
        painter.fillRect(device.rect().adjusted(0, 0, 0, -prog_h), brush)
        color = color.copy(
            0, (color.height() - self.sizeHint().height()) // 2,
            color.width(), self.sizeHint().height()
        )
        brush.setTexture(color)
        painter.fillRect(device.rect().adjusted(0, device.height() - prog_h, 0, 0), brush)
        painter.end()
        device.setDevicePixelRatio(color.devicePixelRatioF())
        return device
