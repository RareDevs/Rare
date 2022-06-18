from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPaintEvent, QPainter, QPixmap, QPen, QFont, QColor
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QWidget
from legendary.models.game import Game

from rare.shared import LegendaryCoreSingleton
from rare.shared.image_manager import ImageManagerSingleton, ImageSize
from rare.utils.utils import (
    optimal_text_background,
    text_color_for_background,
)


class InstallingGameWidget(QWidget):
    game: Game = None

    def __init__(self):
        super(InstallingGameWidget, self).__init__()
        self.setObjectName("game_widget_icon")
        self.setProperty("noBorder", 1)
        self.setLayout(QVBoxLayout())

        self.core = LegendaryCoreSingleton()

        self.pixmap = QPixmap()
        self.image_widget = PaintWidget()
        self.setContentsMargins(0, 0, 0, 0)
        self.image_widget.setFixedSize(ImageSize.Display.size)
        self.layout().addWidget(self.image_widget)

        self.title_label = QLabel(f"<h4>Error</h4>")
        self.title_label.setAutoFillBackground(False)
        self.title_label.setWordWrap(True)
        self.title_label.setFixedWidth(175)
        minilayout = QHBoxLayout()
        self.setObjectName("game_widget")
        minilayout.addWidget(self.title_label)
        self.layout().addLayout(minilayout)

    def set_game(self, app_name):
        if not app_name:
            self.game = None
            return
        self.game = self.core.get_game(app_name)
        self.title_label.setText(f"<h4>{self.game.app_title}</h4>")

        self.image_widget.set_game(self.game.app_name)

    def set_status(self, s: int):
        self.image_widget.progress = s
        self.image_widget.repaint()


class PaintWidget(QWidget):
    color_image: QPixmap
    bw_image: QPixmap
    progress: int = 0

    def __init__(self):
        super(PaintWidget, self).__init__()
        self.core = LegendaryCoreSingleton()
        self.image_manager = ImageManagerSingleton()

    def set_game(self, app_name: str):
        game = self.core.get_game(app_name, False)
        self.color_image = self.image_manager.get_pixmap(game.app_name, color=False)
        self.color_image = self.color_image.scaled(
            ImageSize.Display.size, transformMode=Qt.SmoothTransformation
        )
        self.setFixedSize(ImageSize.Display.size)
        self.bw_image = self.image_manager.get_pixmap(app_name, color=False)
        self.bw_image = self.bw_image.scaled(
            ImageSize.Display.size, transformMode=Qt.SmoothTransformation
        )
        self.progress = 0

        pixel_list = []
        for x in range(self.color_image.width()):
            for y in range(self.color_image.height()):
                # convert pixmap to qimage, get pixel and remove alpha channel
                pixel_list.append(
                    self.color_image.toImage().pixelColor(x, y).getRgb()[:-1]
                )

        self.rgb_tuple = optimal_text_background(pixel_list)

    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(self.rect(), self.bw_image)

        w = self.bw_image.width() * self.progress // 100

        painter.drawPixmap(
            0,
            0,
            w,
            self.color_image.height(),
            self.color_image.copy(QRect(0, 0, w, self.color_image.height())),
        )

        # Draw Circle
        pen = QPen(QColor(*self.rgb_tuple), 3)
        painter.setPen(pen)
        painter.setBrush(QColor(*self.rgb_tuple))
        painter.drawEllipse(
            int(self.width() / 2) - 20, int(self.height() / 2) - 20, 40, 40
        )

        # draw text
        painter.setPen(QColor(*text_color_for_background(self.rgb_tuple)))
        painter.setFont(QFont(None, 16))
        painter.drawText(a0.rect(), Qt.AlignCenter, f"{self.progress}%")
        painter.end()
