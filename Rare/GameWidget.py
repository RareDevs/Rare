import qtawesome as qta
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton


class GameWidget(QWidget):
    def __init__(self, game):
        super(GameWidget, self).__init__()
        # self.setStyleSheet("border:1px solid rgb(0, 0, 0)")

        self.title = game.title
        self.version = game.version

        self.layout = QHBoxLayout()


        self.pixmap = QPixmap(f"../images/{game.app_name}/FinalArt.png")
        self.pixmap = self.pixmap.scaled(240, 320)
        self.image = QLabel()
        self.image.setPixmap(self.pixmap)
        self.layout.addWidget(self.image)

        ##Layout on the right
        self.childLayout = QVBoxLayout()

        self.childLayout.addWidget(QLabel(f"<h1>{self.title}</h1>"))
        play_icon = qta.icon('fa5s.play')

        self.launch_button = QPushButton(play_icon, "Launch")
        self.launch_button.clicked.connect(self.launch)
        self.wine_rating = QLabel("Wine Rating: Comming Soon")
        self.version_label = QLabel("Version: " + str(self.version))

        self.childLayout.addWidget(self.launch_button)
        self.childLayout.addWidget(self.wine_rating)
        self.childLayout.addWidget(self.version_label)

        self.childLayout.addStretch(1)
        # self.layout.addWidget(QLabel(game.title))
        self.layout.addLayout(self.childLayout)
        self.setLayout(self.layout)

    def launch(self):
        print(f"launch {self.title}")
