import logging
import os
import platform
import sys
import time
import traceback
from argparse import Namespace

import legendary
from PySide6 import __version__ as PYSIDE_VERSION_STR
from PySide6.QtCore import __version__ as QT_VERSION_STR
from PySide6.QtCore import (
    QSettings,
    QTranslator,
    QObject,
    Signal,
    Slot,
    Qt,
    QLibraryInfo,
    QLocale,
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

import rare.resources.resources
from rare.models.options import options
from rare.utils import paths
from rare.utils.misc import set_color_pallete, set_style_sheet, get_static_style


class RareAppException(QObject):
    exception = Signal(object, object, object)

    def __init__(self, parent=None):
        super(RareAppException, self).__init__(parent=parent)
        self.logger = logging.getLogger(type(self).__name__)
        sys.excepthook = self._excepthook
        self.exception.connect(self._on_exception)

    def _excepthook(self, exc_type: object, exc_value: object, exc_tb: object):
        self.exception.emit(exc_type, exc_value, exc_tb)

    def _handler(self, exc_type, exc_value, exc_tb) -> bool:
        return False

    @Slot(object, object, object)
    def _on_exception(self, exc_type, exc_value, exc_tb):
        message = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        if self._handler(exc_type, exc_value, exc_tb):
            return
        self.logger.fatal(message)
        action = QMessageBox.warning(
            None, exc_type.__name__, message,
            buttons=QMessageBox.StandardButton.Ignore | QMessageBox.StandardButton.Abort,
            defaultButton=QMessageBox.StandardButton.Abort
        )
        if action == QMessageBox.StandardButton.Abort:
            QApplication.instance().quit()


class RareApp(QApplication):
    def __init__(self, args: Namespace, log_file: str):
        super(RareApp, self).__init__(sys.argv)
        self.logger = logging.getLogger(type(self).__name__)
        self._hook = RareAppException(self)
        self.setQuitOnLastWindowClosed(False)
        self.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)

        self.setDesktopFileName("rare")
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
        else:
            logging.basicConfig(
                format="[%(name)s] %(levelname)s: %(message)s",
                level=logging.INFO,
                stream=sys.stderr,
            )
            file_handler.setLevel(logging.DEBUG)
            logging.root.addHandler(file_handler)
        self.logger.info(
            f"Launching Rare version {rare.__version__} Codename: {rare.__codename__}\n"
            f" - Using Legendary {legendary.__version__} Codename: {legendary.__codename__} as backend\n"
            f" - Operating System: {platform.system()}, Python version: {platform.python_version()}\n"
            f" - Running {sys.executable} {' '.join(sys.argv)}\n"
            f" - Qt version: {QT_VERSION_STR}, PySide6 version: {PYSIDE_VERSION_STR}"
        )

        self.settings = QSettings(self)

        # Style
        # lk: this is a bit silly but serves well until we have a class
        # lk: store the default qt style name from the system on startup as a property for later reference
        self.setProperty("rareDefaultQtStyle", self.style().objectName())
        if (
                self.settings.value(options.style_sheet.key, None) is None
                and self.settings.value(options.color_scheme.key, None) is None
        ):
            self.settings.setValue(options.color_scheme.key, options.color_scheme.default)
            self.settings.setValue(options.style_sheet.key, options.style_sheet.default)

        if color_scheme := self.settings.value(options.color_scheme.key, False):
            self.settings.setValue(options.style_sheet.key, "")
            set_color_pallete(str(color_scheme))
        elif style_sheet := self.settings.value(options.style_sheet.key, False):
            self.settings.setValue(options.color_scheme.key, "")
            set_style_sheet(str(style_sheet))
        else:
            self.setStyleSheet(get_static_style())
        self.setWindowIcon(QIcon(":/images/Rare.png"))

    def load_translator(self, lang: str):
        # translator for qt stuff
        locale = QLocale(lang)
        self.logger.info("Using locale: %s", locale.name())
        translations = {
            "qtbase": QLibraryInfo.location(QLibraryInfo.LibraryPath.TranslationsPath),
            "rare": os.path.join(paths.resources_path, "languages"),
        }
        for filename, path in translations.items():
            translator = QTranslator(self)
            if translator.load(locale, filename, "_", path):
                self.logger.debug("Loaded translation file: %s", translator.filePath())
                self.installTranslator(translator)
            else:
                self.logger.info("Couldn't find translation for locale: %s", locale.name())
                translator.deleteLater()
