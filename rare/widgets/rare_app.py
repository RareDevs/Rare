import os
import sys
from logging import getLogger

from PyQt5.QtCore import Qt, QSettings, QTranslator
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

# noinspection PyUnresolvedReferences
from legendary.core import LegendaryCore

import rare.resources.resources
from rare.utils.paths import resources_path
from rare.utils.misc import set_color_pallete, set_style_sheet


class RareApp(QApplication):
    logger = getLogger("RareApp")

    def __init__(self):
        super(RareApp, self).__init__(sys.argv)
        self.setQuitOnLastWindowClosed(False)
        self.core = LegendaryCore()
        if hasattr(Qt, "AA_UseHighDpiPixmaps"):
            self.setAttribute(Qt.AA_UseHighDpiPixmaps)

        self.setApplicationName("Rare")
        self.setOrganizationName("Rare")
        self.settings = QSettings()

        # Translator
        self.translator = QTranslator()
        self.qt_translator = QTranslator()

        # Style
        # lk: this is a bit silly but serves well until we have a class
        # lk: store the default qt style name from the system on startup as a property for later reference
        self.setProperty("rareDefaultQtStyle", self.style().objectName())

        if (
                self.settings.value("color_scheme", None) is None
                and self.settings.value("style_sheet", None) is None
        ):
            self.settings.setValue("color_scheme", "")
            self.settings.setValue("style_sheet", "RareStyle")

        if color_scheme := self.settings.value("color_scheme", False):
            self.settings.setValue("style_sheet", "")
            set_color_pallete(color_scheme)
        elif style_sheet := self.settings.value("style_sheet", False):
            self.settings.setValue("color_scheme", "")
            set_style_sheet(style_sheet)
        self.setWindowIcon(QIcon(":/images/Rare.png"))

    def load_translator(self, lang: str):
        if os.path.isfile(f := os.path.join(resources_path, "languages", f"{lang}.qm")):
            self.translator.load(f)
            self.logger.info(f"Your language is supported: {lang}")
        elif not lang == "en":
            self.logger.info("Your language is not supported")
        self.installTranslator(self.translator)

        # translator for qt stuff
        if os.path.isfile(f := os.path.join(resources_path, f"qt_{lang}.qm")):
            self.qt_translator = QTranslator()
            self.qt_translator.load(f)
            self.installTranslator(self.qt_translator)
