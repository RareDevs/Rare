import json
import os
from logging import getLogger

from PyQt5.QtWidgets import *
from legendary.core import LegendaryCore

from Rare.utils import legendaryUtils

logger = getLogger("ImportDialog")


class ImportDialog(QDialog):
    def __init__(self, core: LegendaryCore):
        super(ImportDialog, self).__init__()
        self.imported = False
        self.core = core
        self.title_text = QLabel(self.tr("Select Path"))
        self.path_field = QLineEdit()
        self.info_text = QLabel("")
        self.import_button = QPushButton(self.tr("Import"))
        self.import_button.clicked.connect(self.button_click)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.title_text)
        self.layout.addWidget(self.path_field)
        self.layout.addWidget(self.info_text)
        self.layout.addWidget(self.import_button)

        self.setLayout(self.layout)

    def button_click(self):
        if self.import_game():
            self.imported = True
            self.close()
        else:
            self.info_text.setText(self.tr("Failed to import Game"))

    def import_game(self):
        path = self.path_field.text()
        print()
        if not path.endswith("/"):
            path = path + "/"
        file = ""

        for i in os.listdir(os.path.join(path, ".egstore")):
            if i.endswith(".mancpn"):
                file = path + ".egstore/" + i
                break
        else:
            logger.warning("File was not found")
            return False
        app_name = json.load(open(file, "r"))["AppName"]
        if legendaryUtils.import_game(self.core, app_name=app_name, path=path):
            return True
        else:
            logger.warning("Failed to import")
            return False

    def import_dialog(self):
        self.exec_()
        return self.imported