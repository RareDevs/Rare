import os
from logging import getLogger

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QFormLayout, QGroupBox, QLineEdit, QPushButton, \
    QLabel, QCheckBox

from Rare.utils import legendaryConfig


class SettingsForm(QGroupBox):
    config: dict

    def __init__(self, app_name: str):
        self.app_name = app_name
        self.logger = getLogger(f"{app_name} Settings")
        config: dict
        super(SettingsForm, self).__init__(f'Settings for Game {self.app_name}')
        self.config = legendaryConfig.get_config()
        if not self.config.get(self.app_name):
            self.config[self.app_name] = {}
        if not self.config[self.app_name].get("wine_executable"):
            self.config[self.app_name]["wine_executable"] = ""
        if not self.config[self.app_name].get("wine_prefix"):
            self.config[self.app_name]["wine_prefix"] = ""
        if not self.config[self.app_name].get("language"):
            self.config[self.app_name]["language"] = ""
        # if not self.config["Legendary"].get("offline"):
        #     self.config["Legendary"]["offline"] = ""

        env_vars = self.config.get(f"{self.app_name}.env")
        if env_vars:
            self.table = QTableWidget(len(env_vars), 2)
            for i, label in enumerate(env_vars):
                self.table.setItem(i, 0, QTableWidgetItem(label))
                self.table.setItem(i, 1, QTableWidgetItem(env_vars[label]))

        else:
            self.table = QTableWidget(0, 2)

        self.table.setHorizontalHeaderLabels(["Variable", "Value"])

        self.form = QFormLayout()

        self.game_conf_wine_prefix = QLineEdit(self.config[self.app_name]["wine_prefix"])
        self.game_conf_wine_prefix.setPlaceholderText("Default")
        self.game_conf_wine_exec = QLineEdit(self.config[self.app_name]["wine_executable"])
        self.game_conf_wine_exec.setPlaceholderText("Default")
        self.language = QLineEdit(self.config[self.app_name]["language"])
        self.language.setPlaceholderText("Default")

        # self.offline = QCheckBox(self.config["offline"] == "false")


        self.add_button = QPushButton("Add Environment Variable")
        self.delete_env_var = QPushButton("Delete selected Variable")
        self.delete_env_var.clicked.connect(self.delete_var)
        self.add_button.clicked.connect(self.add_variable)

        if os.name != "nt":
            self.form.addRow(QLabel("Default Wineprefix"), self.game_conf_wine_prefix)
            self.form.addRow(QLabel("Wine executable"), self.game_conf_wine_exec)
        # self.form.addRow(QLabel("Offline"), self.offline)
        self.form.addRow(QLabel("Environment Variables"), self.table)
        self.form.addRow(QLabel("Add Variable"), self.add_button)
        self.form.addRow(QLabel("Delete Variable"), self.delete_env_var)
        self.form.addRow(QLabel("language"), self.language)
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
        self.logger.info("Updating Game Settings")

        # Wine exec
        if not self.config.get(self.app_name):
            self.config[self.app_name] = {}
        if self.game_conf_wine_exec.text() != "":
            self.config[self.app_name]["wine_executable"] = self.game_conf_wine_exec.text()
        elif "wine_executable" in self.config[self.app_name]:
            self.config[self.app_name].pop("wine_executable")

        # Wineprefix
        if self.game_conf_wine_prefix.text() != '':
            self.config[self.app_name]["wine_prefix"] = self.game_conf_wine_prefix.text()
            pass
        elif "wine_prefix" in self.config[self.app_name]:
            self.config[self.app_name].pop("wine_prefix")

        # language
        if self.language.text() != "":
            self.config[self.app_name]["language"] = self.language.text()
        elif "language" in self.config[self.app_name]:
            self.config[self.app_name].pop("language")

        # Env vars
        if self.table.rowCount() > 0:
            self.config[f"{self.app_name}.env"] = {}
            for row in range(self.table.rowCount()):
                self.config[f"{self.app_name}.env"][self.table.item(row, 0).text()] = self.table.item(row, 1).text()
        elif f"{self.app_name}.env" in self.config:
            self.config.pop(f"{self.app_name}.env")

        if self.config.get(self.app_name) == {}:
            self.config.pop(self.app_name)
        legendaryConfig.set_config(self.config)
        print(self.config)