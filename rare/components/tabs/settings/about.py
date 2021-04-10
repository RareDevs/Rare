import webbrowser

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from rare import __version__
from rare.utils.utils import get_latest_version


def versiontuple(v):
    try:
        return tuple(map(int, (v.split("."))))
    except:
        return tuple((9, 9, 9))  # It is a beta version and newer


class About(QWidget):
    def __init__(self):
        super(About, self).__init__()
        self.layout = QVBoxLayout()

        self.title = QLabel("<h2>About</h2>")
        self.layout.addWidget(self.title)

        self.version = QLabel("Version: " + __version__)
        self.layout.addWidget(self.version)
        latest_tag = get_latest_version()
        self.update_available = versiontuple(latest_tag) > versiontuple(__version__)
        if self.update_available:
            print(f"Update available: {__version__} -> {latest_tag}")
            self.update_available = QLabel(self.tr("Update available: {} -> {}").format(__version__, latest_tag))
            self.layout.addWidget(self.update_available)
            self.open_browser = QPushButton(self.tr("Download latest release"))
            self.layout.addWidget(self.open_browser)
            self.open_browser.clicked.connect(
                lambda: webbrowser.open("https://github.com/Dummerle/Rare/releases/latest"))

        self.dev = QLabel(self.tr("Developer:") + "<a href='https://github.com/Dummerle'>Dummerle</a>")
        self.dev.setToolTip("Github")
        self.dev.setOpenExternalLinks(True)
        self.dev.setWordWrap(True)
        self.layout.addWidget(self.dev)
        self.lgd_dev = QLabel(self.tr("Legendary developer:") + "<a href='https://github.com/derrod/'>derrod</a>")
        self.lgd_dev.setOpenExternalLinks(True)
        self.lgd_dev.setToolTip("Github")
        self.layout.addWidget(self.lgd_dev)
        self.license = QLabel("License: GNU General Public License v3.0")
        self.layout.addWidget(self.license)
        self.info_text = QLabel(
            self.tr("This is a beta version, so you can get bugs. If you get a bug, please report it by creating a "
                    "Issue on <a href='https://github.com/Dummerle/Rare/issues'>Github</a>. You can also contact me "
                    "on Discord (Dummerle#7419). Or you can join the <a href='https://discord.gg/YvmABK9YSk'>Discord server</a>"))
        self.info_text.setWordWrap(True)
        self.info_text.setOpenExternalLinks(True)
        self.layout.addWidget(self.info_text)

        self.layout.addStretch()
        self.setLayout(self.layout)
