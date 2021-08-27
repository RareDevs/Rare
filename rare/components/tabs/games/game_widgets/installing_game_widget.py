from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPaintEvent, QPainter, QPixmap, QPen, QFont, QColor
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QHBoxLayout, QWidget

from custom_legendary.models.game import Game
from rare.utils.utils import get_pixmap, get_uninstalled_pixmap, optimal_text_background, text_color_for_background


class InstallingGameWidget(QGroupBox):
    def __init__(self, game: Game):
        super(InstallingGameWidget, self).__init__()
        self.setObjectName("game_widget_icon")

        self.setLayout(QVBoxLayout())

        self.pixmap = get_pixmap(game.app_name)
        w = 200
        self.pixmap = self.pixmap.scaled(w, int(w * 4 / 3), transformMode=Qt.SmoothTransformation)

        self.image_widget = PaintWidget(self.pixmap, game.app_name)
        self.image_widget.setFixedSize(w, int(w * 4 / 3))
        self.layout().addWidget(self.image_widget)

        self.title_label = QLabel(f"<h4>{game.app_title}</h4>")
        self.title_label.setAutoFillBackground(False)
        self.title_label.setWordWrap(True)
        self.title_label.setFixedWidth(175)
        minilayout = QHBoxLayout()
        self.title_label.setObjectName("game_widget")
        minilayout.addWidget(self.title_label)
        self.layout().addLayout(minilayout)

    def set_game(self, game: Game):
        self.title_label.setText(f"<h4>{game.app_title}</h4>")
        self.pixmap = get_pixmap(game.app_name)
        w = 200
        self.pixmap = self.pixmap.scaled(w, int(w * 4 / 3), transformMode=Qt.SmoothTransformation)
        self.image_widget.set_game(self.pixmap, game.app_name)


class PaintWidget(QWidget):
    def __init__(self, image: QPixmap, app_name):
        super(PaintWidget, self).__init__()
        self.set_game(image, app_name)

    def set_game(self, pixmap: QPixmap, app_name):
        self.image = pixmap
        self.setFixedSize(self.image.size())
        self.new_image = get_uninstalled_pixmap(app_name)
        self.status = 0
        pixel_list = []
        for x in range(self.image.width()):
            for y in range(self.image.height()):
                # convert pixmap to qimage, get pixel and remove alpha channel
                pixel_list.append(self.image.toImage().pixelColor(x, y).getRgb()[:-1])

        self.rgb_tuple = optimal_text_background(pixel_list)

    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter()
        painter.begin(self)
        painter.drawPixmap(self.rect(), self.image)

        w = self.image.width() * (1 - self.status / 100)
        painter.drawPixmap(self.image.width() - w, 0, w, self.image.height(),
                           self.new_image.copy(QRect(self.image.width() - w, 0, w, self.image.height())))

        # Draw Circle
        pen = QPen(QColor(*self.rgb_tuple), 3)
        painter.setPen(pen)
        painter.setBrush(QColor(*self.rgb_tuple))
        painter.drawEllipse(int(self.width() / 2) - 20, int(self.height() / 2) - 20, 40, 40)

        # draw text
        painter.setPen(QColor(*text_color_for_background(self.rgb_tuple)))
        painter.setFont(QFont(None, 16))
        painter.drawText(a0.rect(), Qt.AlignCenter, str(self.status) + "%")
        painter.end()

    def set_status(self, s: int):
        self.status = s
        self.repaint()
