from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPaintEvent, QPainter, QPixmap, QPen, QFont, QColor
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QWidget

from rare import shared
from rare.utils.utils import get_pixmap, optimal_text_background, text_color_for_background, get_uninstalled_pixmap


class InstallingGameWidget(QWidget):
    def __init__(self):
        super(InstallingGameWidget, self).__init__()
        self.setObjectName("game_widget_icon")
        self.setProperty("noBorder", 1)
        self.setLayout(QVBoxLayout())

        self.pixmap = QPixmap()
        w = 200
        # self.pixmap = self.pixmap.scaled(w, int(w * 4 / 3), transformMode=Qt.SmoothTransformation)
        self.image_widget = PaintWidget()
        self.setContentsMargins(4, 4, 4, 4)
        self.image_widget.setFixedSize(w, int(w * 4 / 3))
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
        game = shared.core.get_game(app_name)
        self.title_label.setText(f"<h4>{game.app_title}</h4>")

        self.image_widget.set_game(game.app_name)

    def set_status(self, s: int):
        self.image_widget.progress = s
        self.image_widget.repaint()


class PaintWidget(QWidget):
    color_image: QPixmap
    bw_image: QPixmap
    progress: int = 0

    def __init__(self):
        super(PaintWidget, self).__init__()

    def set_game(self, app_name: str):
        game = shared.core.get_game(app_name, False)
        self.color_image = get_pixmap(game.app_name)
        w = 200
        self.color_image = self.color_image.scaled(w, int(w * 4 // 3), transformMode=Qt.SmoothTransformation)
        self.setFixedSize(self.color_image.size())
        self.bw_image = get_uninstalled_pixmap(app_name)
        self.bw_image = self.bw_image.scaled(w, int(w * 4 // 3), transformMode=Qt.SmoothTransformation)
        self.progress = 0

        pixel_list = []
        for x in range(self.color_image.width()):
            for y in range(self.color_image.height()):
                # convert pixmap to qimage, get pixel and remove alpha channel
                pixel_list.append(self.color_image.toImage().pixelColor(x, y).getRgb()[:-1])

        self.rgb_tuple = optimal_text_background(pixel_list)

    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter()
        painter.begin(self)
        painter.drawPixmap(self.rect(), self.bw_image)

        w = self.bw_image.width() * self.progress // 100

        painter.drawPixmap(0, 0, w, self.color_image.height(),
                           self.color_image.copy(QRect(0, 0, w, self.color_image.height())))

        # Draw Circle
        pen = QPen(QColor(*self.rgb_tuple), 3)
        painter.setPen(pen)
        painter.setBrush(QColor(*self.rgb_tuple))
        painter.drawEllipse(int(self.width() / 2) - 20, int(self.height() / 2) - 20, 40, 40)

        # draw text
        painter.setPen(QColor(*text_color_for_background(self.rgb_tuple)))
        painter.setFont(QFont(None, 16))
        painter.drawText(a0.rect(), Qt.AlignCenter, str(self.progress) + "%")
        painter.end()
