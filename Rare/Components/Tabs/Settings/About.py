from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class About(QWidget):
    def __init__(self):
        super(About, self).__init__()
        self.layout = QVBoxLayout()

        self.title = QLabel("<h2>About</h2>")
        self.layout.addWidget(self.title)

        self.dev = QLabel(self.tr("Developer:")+"<a href='https://github.com/Dummerle'>Dummerle</a>")
        self.dev.setToolTip("Github")
        self.dev.setOpenExternalLinks(True)
        self.dev.setWordWrap(True)
        self.layout.addWidget(self.dev)
        self.lgd_dev = QLabel(self.tr("Legendary developer:")+"<a href='https://github.com/derrod/'>derrod</a>")
        self.lgd_dev.setOpenExternalLinks(True)
        self.lgd_dev.setToolTip("Github")
        self.layout.addWidget(self.lgd_dev)
        self.license = QLabel("License: GNU General Public License v3.0")
        self.layout.addWidget(self.license)
        self.info_text = QLabel(
            self.tr("This is a beta version, so you can get bugs. If you get a bug, please report it by creating a "
                    "Issue on <a href='https://github.com/Dummerle/Rare/issues'>Github</a>. You can also contact me "
                    "on Discord (Dummerle#7419). If you have a feature request, please contact me"))
        self.info_text.setWordWrap(True)
        self.info_text.setOpenExternalLinks(True)
        self.layout.addWidget(self.info_text)

        self.layout.addStretch()
        self.setLayout(self.layout)
