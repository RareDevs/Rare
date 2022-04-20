import logging

import legendary.cli
from PyQt5.QtWidgets import QLabel, QMessageBox
from legendary.cli import LegendaryCLI as LegendaryCLIReal

from .core import LegendaryCore

logger = logging.getLogger('cli')


def get_boolean_choice(message):
    choice = QMessageBox.question(None, "Import DLCs?", message)
    return True if choice == QMessageBox.StandardButton.Yes else False


class UILogHandler(logging.Handler):
    def __init__(self, dest: QLabel):
        super(UILogHandler, self).__init__()
        self.widget = dest

    def emit(self, record: logging.LogRecord) -> None:
        self.widget.setText(record.getMessage())


class LegendaryCLI(LegendaryCLIReal):

    def __init__(self):
        self.core = None
        self.logger = logging.getLogger('cli')
        self.logging_queue = None

    def import_game(self, args):
        handler = UILogHandler(args.log_dest)
        logger.addHandler(handler)
        old_choice = legendary.cli.get_boolean_choice
        legendary.cli.get_boolean_choice = get_boolean_choice
        super(LegendaryCLI, self).import_game(args)
        legendary.cli.get_boolean_choice = old_choice
        logger.removeHandler(handler)
