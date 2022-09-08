import logging
import os
import platform
import sys
import time
from argparse import Namespace

import legendary
from PyQt5.QtCore import Qt, QSettings, QTranslator, QT_VERSION_STR, PYQT_VERSION_STR
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

import rare.resources.resources
from rare.utils import paths
from rare.utils.misc import set_color_pallete, set_style_sheet


class RareApp(QApplication):
    logger = logging.getLogger("RareApp")

    def __init__(self, args: Namespace, log_file: str):
        super(RareApp, self).__init__(sys.argv)
        self.setQuitOnLastWindowClosed(False)
        if hasattr(Qt, "AA_UseHighDpiPixmaps"):
            self.setAttribute(Qt.AA_UseHighDpiPixmaps)

        self.setApplicationName("Rare")
        self.setOrganizationName("Rare")

        # Create directories after QStandardPaths has been initialized
        paths.create_dirs()

        # Clean any existing logging handlers from library imports
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        start_time = time.strftime("%y-%m-%d--%H-%M")  # year-month-day-hour-minute
        file_handler = logging.FileHandler(
            filename=os.path.join(paths.log_dir(), log_file.format(start_time)),
            encoding="utf-8",
        )
        file_handler.setFormatter(fmt=logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))

        # Set up common logging channel to stderr
        if args.debug:
            logging.basicConfig(
                format="[%(name)s] %(levelname)s: %(message)s",
                level=logging.DEBUG,
                stream=sys.stderr,
            )
            file_handler.setLevel(logging.DEBUG)
            logging.root.addHandler(file_handler)
            logging.getLogger().setLevel(level=logging.DEBUG)
            # keep requests, asyncio and pillow quiet
            logging.getLogger("requests").setLevel(logging.WARNING)
            logging.getLogger("urllib3").setLevel(logging.WARNING)
            logging.getLogger("asyncio").setLevel(logging.WARNING)
            self.logger.info(
                f"Launching Rare version {rare.__version__} Codename: {rare.code_name}\n"
                f" - Using Legendary {legendary.__version__} Codename: {legendary.__codename__} as backend\n"
                f" - Operating System: {platform.system()}, Python version: {platform.python_version()}\n"
                f" - Running {sys.executable} {' '.join(sys.argv)}\n"
                f" - Qt version: {QT_VERSION_STR}, PyQt version: {PYQT_VERSION_STR}"
            )
        else:
            logging.basicConfig(
                format="[%(name)s] %(levelname)s: %(message)s",
                level=logging.INFO,
                stream=sys.stderr,
            )
            file_handler.setLevel(logging.DEBUG)
            logging.root.addHandler(file_handler)
            self.logger.info(f"Launching Rare version {rare.__version__}")
            self.logger.info(f"Operating System: {platform.system()}")

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
        if os.path.isfile(f := os.path.join(paths.resources_path, "languages", f"{lang}.qm")):
            self.translator.load(f)
            self.logger.info(f"Your language is supported: {lang}")
        elif not lang == "en":
            self.logger.info("Your language is not supported")
        self.installTranslator(self.translator)

        # translator for qt stuff
        if os.path.isfile(f := os.path.join(paths.resources_path, f"qt_{lang}.qm")):
            self.qt_translator = QTranslator()
            self.qt_translator.load(f)
            self.installTranslator(self.qt_translator)
