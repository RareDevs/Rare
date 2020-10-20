import qtawesome as qta
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton


class GameWidget(QWidget):
    def __init__(self, game):
        super(GameWidget, self).__init__()
        # self.setStyleSheet("border:1px solid rgb(0, 0, 0)")

        self.title = game.title
        self.version = game.version
        self.size = game.install_size

        self.layout = QHBoxLayout()

        pixmap = QPixmap(f"../images/{game.app_name}/FinalArt.png")
        pixmap = pixmap.scaled(240, 320)
        self.image = QLabel()
        self.image.setPixmap(pixmap)
        self.layout.addWidget(self.image)

        ##Layout on the right
        self.childLayout = QVBoxLayout()

        self.childLayout.addWidget(QLabel(f"<h1>{self.title}</h1>"))
        play_icon = qta.icon('fa5s.play')

        self.launch_button = QPushButton(play_icon, "Launch")
        self.launch_button.clicked.connect(self.launch)
        self.wine_rating = QLabel("Wine Rating: " + self.get_rating())
        self.version_label = QLabel("Version: " + str(self.version))
        self.size_label = QLabel(f"Installed size: {round(self.size / (1024 ** 3), 2)} GB")
        self.settings = QPushButton(qta.icon("fa5s.cogs"), " Settings")

        self.childLayout.addWidget(self.launch_button)
        self.childLayout.addWidget(self.wine_rating)
        self.childLayout.addWidget(self.version_label)
        self.childLayout.addWidget(self.size_label)
        self.childLayout.addWidget(self.settings)

        self.childLayout.addStretch(1)
        # self.layout.addWidget(QLabel(game.title))
        self.layout.addLayout(self.childLayout)
        self.setLayout(self.layout)

    def launch(self):
        print(f"launch {self.title}")
        # TODO

    def get_rating(self) -> str:
        return "gold"  # TODO


class UninstalledGameWidget(QWidget):
    def __init__(self, game):
        super(UninstalledGameWidget, self).__init__()
        self.title = game.app_title
        self.layout = QHBoxLayout()

        pixmap = QPixmap(f"../images/{game.app_name}/UninstalledArt.png")
        pixmap = pixmap.scaled(240, 320)
        self.image = QLabel()
        self.image.setPixmap(pixmap)
        self.layout.addWidget(self.image)

        self.layout.addWidget(QLabel(f"<h1>{self.title}</h1>"))
        self.setLayout(self.layout)