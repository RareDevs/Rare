import shutil
from logging import getLogger

from PyQt5.QtWidgets import QGroupBox, QComboBox, QFormLayout, QLineEdit, QLabel, QPushButton

from Rare.Styles import dark
from Rare.utils import RareConfig

logger = getLogger("Rare Settings")


class RareSettingsForm(QGroupBox):
    def __init__(self):
        super(RareSettingsForm, self).__init__("Rare Settings")

        self.rare_form = QFormLayout()
        self.style_combo_box = QComboBox()
        self.style_combo_box.addItems(["Light", "Dark"])
        if RareConfig.THEME == "dark":
            self.style_combo_box.setCurrentIndex(1)

        self.rare_form.addRow(QLabel("Style"), self.style_combo_box)

        self.image_dir_edit = QLineEdit()
        self.image_dir_edit.setPlaceholderText("Image directory")
        self.image_dir_edit.setText(RareConfig.IMAGE_DIR)

        self.rare_form.addRow(QLabel("Image Directory"), self.image_dir_edit)
        self.submit_button = QPushButton("Update Rare Settings")
        self.submit_button.clicked.connect(self.update_rare_settings)
        self.rare_form.addRow(self.submit_button)
        self.setLayout(self.rare_form)

    def update_rare_settings(self):
        logger.info("Update Rare settings")
        config = {"Rare": {}}
        if self.style_combo_box.currentIndex() == 1:
            self.parent().parent().parent().setStyleSheet(dark)
            config["Rare"]["theme"] = "dark"
        else:
            self.parent().parent().parent().setStyleSheet("")
            config["Rare"]["theme"] = "light"
        config["Rare"]["IMAGE_DIR"] = self.image_dir_edit.text()

        if self.image_dir_edit.text() != RareConfig.IMAGE_DIR:
            shutil.move(RareConfig.IMAGE_DIR, self.image_dir_edit.text())
        RareConfig.set_config(config)
