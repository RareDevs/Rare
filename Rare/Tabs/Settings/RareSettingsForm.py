import os
import shutil
from logging import getLogger

from PyQt5.QtWidgets import QGroupBox, QComboBox, QFormLayout, QLabel, QPushButton, QFileDialog

from Rare import style_path
from Rare.ext.QtExtensions import PathEdit
from Rare.utils import RareConfig

logger = getLogger("Rare Settings")


class RareSettingsForm(QGroupBox):
    def __init__(self):
        super(RareSettingsForm, self).__init__("Rare Settings")

        self.rare_form = QFormLayout()
        self.style_combo_box = QComboBox()
        self.style_combo_box.addItems([self.tr("Light"), self.tr("Dark")])
        if RareConfig.THEME == "default":
            self.style_combo_box.setCurrentIndex(1)

        self.rare_form.addRow(QLabel("Style"), self.style_combo_box)

        self.image_dir_edit = PathEdit(RareConfig.IMAGE_DIR, QFileDialog.Directory, self.tr("Choose Folder"))
        self.image_dir_edit.setPlaceholderText(self.tr("Image directory"))
        # self.image_dir_edit.setText(RareConfig.IMAGE_DIR)

        self.rare_form.addRow(QLabel(self.tr("Image Directory")), self.image_dir_edit)
        self.submit_button = QPushButton(self.tr("Update Rare Settings"))
        self.submit_button.clicked.connect(self.update_rare_settings)
        self.rare_form.addRow(self.submit_button)
        self.setLayout(self.rare_form)

    def update_rare_settings(self):
        logger.info("Update Rare settings")
        config = {"Rare": {}}
        if self.style_combo_box.currentIndex() == 1:
            self.parent().parent().parent().parent().parent().setStyleSheet(open(style_path+"dark.qss").read())
            config["Rare"]["theme"] = "default"
        else:
            self.parent().parent().parent().setStyleSheet("")
            config["Rare"]["theme"] = "light"
        config["Rare"]["IMAGE_DIR"] = self.image_dir_edit.text()

        if self.image_dir_edit.text() != RareConfig.IMAGE_DIR:
            shutil.move(RareConfig.IMAGE_DIR, self.image_dir_edit.text())
        RareConfig.set_config(config)
