import json
import os
import subprocess

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QStackedLayout, QScrollArea

import Rare
from Rare import FlowLayout
from Rare.ShowGame import GameWidget


class BodyGames(QScrollArea):
    def __init__(self, allGames, installedGames):
        super().__init__()
        self.allGames = allGames
        self.installedGames = installedGames
        self.initUI()

    def initUI(self):
        self.layout = FlowLayout.FlowLayout()
        self.setLayout(self.layout)
        for game in self.allGames:
            self.layout.addWidget(GameWidget(game=game, installed=game['app_name'] in self.installedGames))

    def addImage(self, pathToImage, layout, x, y):
        self.label = Rare.ExtendedQLabel()
        self.label.setPixmap(QPixmap(pathToImage).scaled(240, 320))
        self.label.clicked.connect(lambda: self.clickedGame(pathToImage.split('/', 2)[1]))
        self.label.rightClicked.connect(lambda: self.gameSettings(pathToImage.split('/', 2)[1]))
        layout.addWidget(self.label, x, y)

    def clickedGame(self, game):
        self.game = game
        if self.game in self.installedGames:
            self.launchGame(self.game)
        else:
            self.installGame(self.game)

    # def launchGame(self, game):
    # self.window = LaunchWindow(game)
    # self.window.show()
    # self.window.outputWindow.appendPlainText('> legendary launch ' + game + '\n')
    # self.window.reader.start('legendary', ['launch', game])

    def installGame(self, game):
        self.window = Rare.InstallWindow(game)
        self.window.show()

    def gameSettings(self, game):
        self.window = Rare.GameSettingsWindow(game)
        self.window.show()


class Body(QStackedLayout):
    def __init__(self):
        super(Body, self).__init__()

        all, installed = self.get_games()
        self.addWidget(BodyGames(all, installed))

    def get_games(self):
        all_games = []
        for filename in os.listdir(os.path.expanduser("~") + '/.config/legendary/metadata/'):
            with open(os.path.expanduser("~") + '/.config/legendary/metadata/' + filename, 'r') as f:
                game = json.load(f)
                all_games.append(game)
                try:
                    os.mkdir('images/' + game["app_name"])
                except OSError:
                    pass

        # print('Parsing installed games')
        installedGames = []
        for line in subprocess.Popen('legendary list-installed --csv | tail -n +2', shell=True,
                                     stdout=subprocess.PIPE, universal_newlines=True).stdout:
            installedGames.append(line.split(',', 1)[0])

        return all_games, installedGames
