from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QFrame
from legendary.models.game import Game

from rare.shared import LegendaryCoreSingleton
from rare.shared.image_manager import ImageManagerSingleton, ImageSize
from rare.widgets.elide_label import ElideLabel
from .library_widget import LibraryWidget


class InstallingGameWidget(QFrame):
    game: Game = None

    def __init__(self):
        super(InstallingGameWidget, self).__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setFixedWidth(ImageSize.Display.size.width())
        self.setObjectName("game_widget_icon")

        self.core = LegendaryCoreSingleton()
        self.image_manager = ImageManagerSingleton()

        self.pixmap = QPixmap()
        self.image = LibraryWidget(parent=self)
        self.image.setFixedSize(ImageSize.Display)
        layout.addWidget(self.image)

        miniwidget = QWidget(self)
        miniwidget.setFixedWidth(ImageSize.Display.size.width())
        minilayout = QHBoxLayout()
        minilayout.setContentsMargins(0, 0, 0, 0)
        minilayout.setSpacing(0)
        miniwidget.setLayout(minilayout)

        self.title_label = ElideLabel(f"<h4>Error</h4>", parent=miniwidget)
        self.title_label.setAlignment(Qt.AlignTop)
        self.title_label.setObjectName("game_widget")
        minilayout.addWidget(self.title_label, stretch=2)

        minilayout.setAlignment(Qt.AlignTop)
        layout.addWidget(miniwidget)

        self.setLayout(layout)

    def set_game(self, app_name):
        if not app_name:
            self.game = None
            return
        self.game = self.core.get_game(app_name)
        self.title_label.setText(f"<h4>{self.game.app_title}</h4>")
        self.image.hideProgress(True)
        self.image.showProgress(
            self.image_manager.get_pixmap(app_name, color=True),
            self.image_manager.get_pixmap(app_name, color=False),
        )

    def set_status(self, s: int):
        self.image.updateProgress(s)
