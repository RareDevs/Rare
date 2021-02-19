import os
import shutil
from logging import getLogger

from PyQt5.QtCore import QSettings, QTranslator
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog, QComboBox, QApplication, QPushButton

from Rare.utils.QtExtensions import PathEdit
from Rare.utils.utils import get_lang, get_possible_langs

logger = getLogger("RareSettings")
class RareSettings(QWidget):
    def __init__(self):
        super(RareSettings, self).__init__()
        self.layout = QVBoxLayout()
        self.title = QLabel("<h2>Rare settings</h2>")
        self.layout.addWidget(self.title)
        settings = QSettings()
        img_dir = settings.value("img_dir", type=str)
        language = settings.value("language", type=str)
        # default settings
        if not img_dir:
            settings.setValue("img_dir", os.path.expanduser("~/.cache/rare/"))
        if not language:
            settings.setValue("language", get_lang())
        del settings
        # select Image dir
        self.select_path = PathEdit(img_dir, type_of_file=QFileDialog.DirectoryOnly)
        self.select_path.text_edit.textChanged.connect(lambda t: self.save_path_button.setDisabled(False))
        self.save_path_button = QPushButton("Save")
        self.save_path_button.clicked.connect(self.save_path)
        self.img_dir = SettingsWidget("Image Directory", self.select_path, self.save_path_button)
        self.layout.addWidget(self.img_dir)

        # Select lang
        self.select_lang = QComboBox()
        languages = ["English", "Deutsch"]
        self.select_lang.addItems(languages)
        if language in get_possible_langs():
            if language == "de":
                self.select_lang.setCurrentIndex(1)
            elif language == "en":
                self.select_lang.setCurrentIndex(0)
        else:
            self.select_lang.setCurrentIndex(0)
        self.lang_widget = SettingsWidget("Language", self.select_lang)
        self.select_lang.currentIndexChanged.connect(self.update_lang)
        self.layout.addWidget(self.lang_widget)

        self.layout.addStretch()

        self.setLayout(self.layout)

    def save_path(self):
        self.save_path_button.setDisabled(True)
        self.update_path()

    def update_lang(self, i: int):
        settings = QSettings()
        if i == 0:
            settings.setValue("language", "en")
        elif i == 1:
            settings.setValue("language", "de")
        del settings
        self.lang_widget.info_text.setText("Restart Application to activate changes")

    def update_path(self):
        settings = QSettings()
        old_path = settings.value("img_dir", type=str)
        new_path = self.select_path.text()
        settings.setValue("img_dir", new_path)
        print(old_path, new_path)
        del settings
        if old_path != new_path:
            if os.path.exists(new_path):
                os.makedirs(new_path)
            logger.info("Move Images")
            shutil.move(old_path, new_path)





class SettingsWidget(QWidget):
    def __init__(self, text: str, widget: QWidget, accept_button: QPushButton=None):
        super(SettingsWidget, self).__init__()
        self.setObjectName("settings_widget")
        self.layout = QVBoxLayout()
        self.info_text = QLabel("")
        self.layout.addWidget(QLabel(text))
        self.layout.addWidget(widget)
        if accept_button:
            self.layout.addWidget(accept_button)
        self.layout.addWidget(self.info_text)
        self.setLayout(self.layout)
