import os
from logging import getLogger

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QFormLayout, QGroupBox, QLineEdit, QPushButton, \
    QLabel

from Rare.utils import legendaryConfig

logger = getLogger("Legendary Settings")


class LegendarySettingsForm(QGroupBox):
    config: dict

    def __init__(self):
        config: dict
        super(LegendarySettingsForm, self).__init__("Legendary Settings")
        self.config = legendaryConfig.get_config()
        if not self.config.get("Legendary"):
            self.config["Legendary"] = {}
        if not self.config["Legendary"].get("wine_executable"):
            self.config["Legendary"]["wine_executable"] = ""
        if not self.config["Legendary"].get("wine_prefix"):
            self.config["Legendary"]["wine_prefix"] = ""
        if not self.config["Legendary"].get("locale"):
            self.config["Legendary"]["locale"] = ""

        env_vars = self.config.get("default.env")
        if env_vars:
            self.table = QTableWidget(len(env_vars), 2)
            for i, label in enumerate(env_vars):
                self.table.setItem(i, 0, QTableWidgetItem(label))
                self.table.setItem(i, 1, QTableWidgetItem(env_vars[label]))

        else:
            self.table = QTableWidget(0, 2)

        self.table.setHorizontalHeaderLabels(["Variable", "Value"])

        self.form = QFormLayout()

        self.lgd_conf_wine_prefix = QLineEdit(self.config["Legendary"]["wine_prefix"])
        self.lgd_conf_wine_prefix.setPlaceholderText("Default")
        self.lgd_conf_wine_exec = QLineEdit(self.config["Legendary"]["wine_executable"])
        self.lgd_conf_wine_exec.setPlaceholderText("Default")
        self.lgd_conf_locale = QLineEdit(self.config["Legendary"]["locale"])
        self.lgd_conf_locale.setPlaceholderText("Default")

        self.add_button = QPushButton("Add Environment Variable")
        self.delete_env_var = QPushButton("Delete selected Variable")
        self.delete_env_var.clicked.connect(self.delete_var)
        self.add_button.clicked.connect(self.add_variable)

        if os.name != "nt":
            self.form.addRow(QLabel("Default Wineprefix"), self.lgd_conf_wine_prefix)
            self.form.addRow(QLabel("Wine executable"), self.lgd_conf_wine_exec)
        self.form.addRow(QLabel("Environment Variables"), self.table)
        self.form.addRow(QLabel("Add Variable"), self.add_button)
        self.form.addRow(QLabel("Delete Variable"), self.delete_env_var)
        self.form.addRow(QLabel("Locale"), self.lgd_conf_locale)
        self.submit_button = QPushButton("Update")
        self.submit_button.clicked.connect(self.update_legendary_settings)
        self.form.addRow(self.submit_button)
        self.setLayout(self.form)

    def add_variable(self):
        print("add row")
        self.table.insertRow(self.table.rowCount())
        self.table.setItem(self.table.rowCount(), 0, QTableWidgetItem(""))
        self.table.setItem(self.table.rowCount(), 1, QTableWidgetItem(""))

    def delete_var(self):
        self.table.removeRow(self.table.currentRow())

    def update_legendary_settings(self):
        logger.info("Updating Legendary Settings")

        # Wine exec
        if self.lgd_conf_wine_exec.text() != "":
            self.config["Legendary"]["wine_executable"] = self.lgd_conf_wine_exec.text()
        elif "wine_executable" in self.config["Legendary"]:
            self.config["Legendary"].pop("wine_executable")

        # Wineprefix
        if self.lgd_conf_wine_prefix.text() != '':
            self.config["Legendary"]["wine_prefix"] = self.lgd_conf_wine_prefix.text()
        elif "wine_prefix" in self.config["Legendary"]:
            self.config["Legendary"].pop("wine_prefix")

        # Locale
        if self.lgd_conf_locale.text() != "":
            self.config["Legendary"]["locale"] = self.lgd_conf_locale.text()
        elif "locale" in self.config["Legendary"]:
            self.config["Legendary"].pop("locale")

        # Env vars
        if self.table.rowCount() != 0:
            self.config["default.env"] = {}
            for row in range(self.table.rowCount()):
                self.config["default.env"][self.table.item(row, 0).text()] = self.table.item(row, 1).text()
        elif "default.env" in self.config["Legendary"]:
            self.config.pop("default.env")
            print("pop")
        legendaryConfig.set_config(self.config)
        print(self.config)
