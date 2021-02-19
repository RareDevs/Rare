from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLabel


class About(QWidget):
    def __init__(self):
        super(About, self).__init__()
        self.layout = QVBoxLayout()

        self.title = QLabel("<h2>About</h2>")
        self.layout.addWidget(self.title)

        self.setLayout(self.layout)