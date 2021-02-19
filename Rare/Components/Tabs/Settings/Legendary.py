from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLabel


class LegendarySettings(QWidget):
    def __init__(self):
        super(LegendarySettings, self).__init__()
        self.layout = QVBoxLayout()

        self.title = QLabel("<h2>Legendary settings</h2>")
        self.layout.addWidget(self.title)
        
        self.setLayout(self.layout)