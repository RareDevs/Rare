#!/usr/bin/env python

import os
import math
import json
import requests
import configparser
import subprocess
from PIL import Image
from time import sleep
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

print('Rare v1 starting up...')


class MainWindow(QScrollArea):
    def __init__(self, allGames, installedGames):
        super().__init__()
        self.allGames = allGames
        self.installedGames = installedGames
        self.initUI()

    def initUI(self):

        self.widget = QWidget()
        self.layout = QGridLayout()

        self.gamesPerRow = int((ScreenInfo().screenWidth * .7) / 250)

        j = 0
        for game in self.installedGames:
            self.addImage('images/' + game + '/FinalArt.png', self.layout,
                          math.floor(j / self.gamesPerRow), j % self.gamesPerRow)
            j += 1

        for game in self.allGames:
            if not game["app_name"] in self.installedGames:
                self.addImage('images/' + game["app_name"] + '/UninstalledArt.png', self.layout,
                              math.floor(j / self.gamesPerRow), j % self.gamesPerRow)
                j += 1

        self.widget.setLayout(self.layout)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.resize(250 * self.gamesPerRow, int(.7 * ScreenInfo().screenHeight))
        center(self)
        self.setWindowTitle('Rare v1')
        self.setWidget(self.widget)
        self.show()

    def addImage(self, pathToImage, layout, x, y):
        self.label = ExtendedQLabel()
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

    def launchGame(self, game):
        self.window = LaunchWindow(game)
        self.window.show()
        self.window.outputWindow.appendPlainText('> legendary launch ' + game + '\n')
        self.window.reader.start('legendary', ['launch', game])

    def installGame(self, game):
        self.window = InstallWindow(game)
        self.window.show()

    def gameSettings(self, game):
        self.window = GameSettingsWindow(game)
        self.window.show()


class LaunchWindow(QMainWindow):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.initUI()

    def initUI(self):
        self.widget = QWidget()
        self.layout = QVBoxLayout()

        self.outputWindow = TerminalOutput()

        self.reader = ProcessOutputReader()
        self.reader.produce_output.connect(self.outputWindow.append_output)

        self.layout.addWidget(self.outputWindow)

        self.widget.setLayout(self.layout)
        self.setWindowTitle('Launching ' + self.game)
        self.setCentralWidget(self.widget)

        self.resize(int(.3 * ScreenInfo().screenWidth), int(.3 * ScreenInfo().screenHeight))
        center(self)


class InstallWindow(QMainWindow):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.initUI()

    def initUI(self):
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.installConfirmation = QLabel()
        self.installConfirmation.setText('Do you really want to install ' + self.game + '?')
        self.layout.addWidget(self.installConfirmation)
        self.layout.setAlignment(Qt.AlignCenter)

        self.yesButton = QPushButton()
        self.yesButton.setText('Yes')
        self.yesButton.clicked.connect(self.installGame)
        self.noButton = QPushButton()
        self.noButton.setText('No')
        self.noButton.clicked.connect(self.close)
        self.buttonLayout.addWidget(self.yesButton)
        self.buttonLayout.addWidget(self.noButton)
        self.layout.addLayout(self.buttonLayout)

        self.widget.setLayout(self.layout)
        self.setWindowTitle('Install ' + self.game + '?')
        self.setCentralWidget(self.widget)
        self.resize(int(.3 * ScreenInfo().screenWidth), int(.3 * ScreenInfo().screenHeight))
        center(self)

    def installGame(self):
        self.outputWindow = TerminalOutput()
        self.reader = ProcessOutputReader()
        self.reader.produce_output.connect(self.outputWindow.append_output)
        self.reader.start('legendary', ['-y', 'install', self.game])
        self.progressWindowCancel = QPushButton()
        self.progressWindowCancel.setText('Cancel')
        self.progressWindowCancel.pressed.connect(lambda: (self.reader.close(), self.progressWindow.close()))

        self.progressWindow = QMainWindow()
        self.progressWindowWidget = QWidget()
        self.progressWindowLayout = QVBoxLayout()
        self.progressWindowLayout.addWidget(self.outputWindow)
        self.progressWindowLayout.addWidget(self.progressWindowCancel)

        self.progressWindowWidget.setLayout(self.progressWindowLayout)
        self.progressWindow.setCentralWidget(self.progressWindowWidget)
        self.progressWindow.setWindowTitle('Installing ' + self.game)
        self.progressWindow.resize(int(.3 * ScreenInfo().screenWidth), int(.3 * ScreenInfo().screenHeight))
        center(self.progressWindow)
        self.progressWindow.show()
        self.close()


class GameSettingsWindow(QMainWindow):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.initUI()

    def initUI(self):
        self.widget = QWidget()
        self.layout = QGridLayout()

        self.config = configparser.ConfigParser()
        self.config.optionxform = lambda option: option
        self.config.read(os.path.expanduser("~") + '/.config/legendary/config.ini')

        self.wineSetting_label = QLabel()
        self.wineSetting_label.setText('Wine executable: ')
        self.wineSetting = QLineEdit()
        self.wrapperSetting_label = QLabel()
        self.wrapperSetting_label.setText('Wrapper: ')
        self.wrapperSetting = QLineEdit()
        self.noWineSetting_label = QLabel()
        self.noWineSetting_label.setText('Don\'t use \'wine_executable\'')
        self.noWineSetting = QCheckBox()

        self.OKButton = QPushButton()
        self.OKButton.setText('OK')
        self.OKButton.clicked.connect(lambda: (self.writeSettings(self.config), self.close()))
        self.cancelButton = QPushButton()
        self.cancelButton.setText('Cancel')
        self.cancelButton.clicked.connect(self.close)
        self.applyButton = QPushButton()
        self.applyButton.setText('Apply')
        self.applyButton.clicked.connect(lambda: self.writeSettings(self.config))

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.OKButton)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addWidget(self.applyButton)

        if self.game not in self.config:
            self.config[self.game] = {}
        self.gameSettings = self.config[self.game]

        self.wineSetting.setText(self.gameSettings.get('wine_executable', ''))
        self.wineSetting.setPlaceholderText('Unset, [default] value: \'' +
                                            self.config['default'].get('wine_executable', '') + '\'')
        self.wrapperSetting.setText(self.gameSettings.get('wrapper', ''))
        self.wrapperSetting.setPlaceholderText('Unset, not using default value '
                                               '(not supported for \'wrapper\' and \'no_wine\'')
        self.noWineSetting.setChecked(self.gameSettings.getboolean('no_wine', False))

        self.layout.addWidget(self.wineSetting_label, 0, 0)
        self.layout.addWidget(self.wineSetting, 0, 1)
        self.layout.addWidget(self.wrapperSetting_label, 1, 0)
        self.layout.addWidget(self.wrapperSetting, 1, 1)
        self.layout.addWidget(self.noWineSetting_label, 2, 0)
        self.layout.addWidget(self.noWineSetting, 2, 1)
        self.layout.addLayout(self.buttonLayout, 3, 1)

        self.widget.setLayout(self.layout)
        self.setWindowTitle('Settings for ' + self.game)
        self.setCentralWidget(self.widget)
        self.resize(int(.4 * ScreenInfo().screenWidth), int(.3 * ScreenInfo().screenHeight))
        center(self)

    def writeSettings(self, configToSave):
        if not self.wineSetting.text() == '':
            self.config.set(self.game, 'wine_executable', self.wineSetting.text())
        if not self.wrapperSetting.text() == '':
            self.config.set(self.game, 'wrapper', self.wrapperSetting.text())
        self.config.set(self.game, 'no_wine', str(self.noWineSetting.isChecked()))
        with open(os.path.expanduser("~") + '/.config/legendary/config.ini', 'w') as configfile:
            configToSave.write(configfile)


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.widget = QWidget()
        self.layout = QVBoxLayout()

        self.loginMessage = QLabel()
        self.loginMessage.setText('You\'re currently not logged in.'
                                  ' Click "Open login window" to open a browser window to login.\n'
                                  'After you do, copy the "sid" value into the Text Input field below'
                                  ' and click "Submit".')
        self.layout.addWidget(self.loginMessage)
        self.loginOpenButton = QPushButton()
        self.loginOpenButton.setText('Open login window')
        self.layout.addWidget(self.loginOpenButton)
        self.loginOpenButton.pressed.connect(lambda: QDesktopServices.openUrl(QUrl(
            'https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect')))
        self.loginInputField = QLineEdit()
        self.loginInputField.setPlaceholderText('Paste the "sid" value here')
        self.layout.addWidget(self.loginInputField)
        self.loginSubmitButton = QPushButton()
        self.loginSubmitButton.setText('Submit')
        self.loginSubmitButton.pressed.connect(lambda: self.tryLogin(self.loginInputField.text()))
        self.layout.addWidget(self.loginSubmitButton)

        self.widget.setLayout(self.layout)
        self.setWindowTitle('Not logged in')
        self.setCentralWidget(self.widget)
        self.resize(int(.4 * ScreenInfo().screenWidth), int(.3 * ScreenInfo().screenHeight))
        center(self)
        self.show()

    def tryLogin(self, sid):
        legendaryProcess = subprocess.Popen('legendary auth --sid ' + sid, shell=True, stdout=subprocess.DEVNULL,
                                            stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
        try:
            legendaryProcess.wait(20)
        except subprocess.TimeoutExpired:
            pass
        if os.path.isfile(os.path.expanduser("~") + '/.config/legendary/user.json'):
            self.close()
            #Run list-games once to get game list + info for newly logged in account
            installedGames = subprocess.Popen('legendary list-games', shell=True,
                                              stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            installedGames.wait()
            startMainProcess(True)
        else:
            self.errorWindow = QMainWindow()
            self.errorWindowWidget = QWidget()
            self.errorWindowLayout = QVBoxLayout()
            self.errorWindow.setCentralWidget(self.errorWindowWidget)
            self.errorWindowWidget.setLayout(self.errorWindowLayout)
            self.errorText = QLabel()
            self.errorText.setText('There was an error logging in.\n'
                                   'Please double-check you typed in the "sid" value.')
            self.errorWindowLayout.addWidget(self.errorText)
            self.errorButton = QPushButton()
            self.errorButton.setText('OK')
            self.errorButton.pressed.connect(self.errorWindow.close)
            self.errorWindowLayout.addWidget(self.errorButton)
            self.errorWindow.resize(int(.2 * ScreenInfo().screenWidth), int(.15 * ScreenInfo().screenHeight))
            center(self.errorWindow)
            self.errorWindow.show()


class ProcessOutputReader(QProcess):
    produce_output = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()

        # merge stderr channel into stdout channel
        self.setProcessChannelMode(QProcess.MergedChannels)

        # prepare decoding process' output to Unicode
        codec = QTextCodec.codecForLocale()
        self._decoder_stdout = codec.makeDecoder()

        self.readyReadStandardOutput.connect(self._ready_read_standard_output)

    @pyqtSlot()
    def _ready_read_standard_output(self):
        raw_bytes = self.readAllStandardOutput()
        text = self._decoder_stdout.toUnicode(raw_bytes)
        self.produce_output.emit(text)


class TerminalOutput(QPlainTextEdit):

    def __init__(self):
        super().__init__()

        self.setReadOnly(True)

        self._cursor_output = self.textCursor()

    @pyqtSlot(str)
    def append_output(self, text):
        self._cursor_output.insertText(text)
        self.scroll_to_last_line()

    def scroll_to_last_line(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.Up if cursor.atBlockStart() else
                            QTextCursor.StartOfLine)
        self.setTextCursor(cursor)


class ExtendedQLabel(QLabel):
    clicked = pyqtSignal()
    rightClicked = pyqtSignal()

    def __init__(self, parent=None):
        QLabel.__init__(self, parent)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.clicked.emit()
        if ev.button() == Qt.RightButton:
            self.rightClicked.emit()


class ScreenInfo():
    def __init__(self):
        self.screenWidth = QDesktopWidget().screenGeometry(-1).width()
        self.screenHeight = QDesktopWidget().screenGeometry(-1).height()


def center(self):
    qr = self.frameGeometry()
    qr.moveCenter(QDesktopWidget().availableGeometry().center())
    self.move(qr.topLeft())


def main():
    # Check if Legendary is installed
    try:
        subprocess.Popen('legendary', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        print('Legendary does not appear to be installed. Install it using\'pip install legendary-gl\'')
        exit(1)

    if os.path.isfile(os.path.expanduser("~") + '/.config/legendary/user.json'):
        startMainProcess()
    else:
        notLoggedIn()

def startMainProcess(loggedIn=False):

    print('Creating directorys')
    try:
        os.mkdir('images')
    except OSError:
        pass

    print('Parsing game metadata')
    allGames = []
    for filename in os.listdir(os.path.expanduser("~") + '/.config/legendary/metadata/'):
        with open(os.path.expanduser("~") + '/.config/legendary/metadata/' + filename, 'r') as f:
            game = json.load(f)
            allGames.append(game)
            try:
                os.mkdir('images/' + game["app_name"])
            except OSError:
                pass

    print('Parsing installed games')
    installedGames = []
    for line in subprocess.Popen('legendary list-installed --csv | tail -n +2', shell=True,
                                 stdout=subprocess.PIPE, universal_newlines=True).stdout:
        installedGames.append(line.split(',', 1)[0])

    print('Downloading and scaling cover images, this could take a little on first boot')
    for game in allGames:
        for image in game["metadata"]["keyImages"]:
            # Check if the game's type is either the background or the logo, since that's the only two images we need
            if image["type"] == "DieselGameBoxTall" or image["type"] == "DieselGameBoxLogo":
                # If a cover was already downloaded, we don't have to download it again
                if not os.path.isfile('images/' + game["app_name"] + '/' + image["type"] + '.png'):
                    print('Downloading ' + image["type"] + ' for ' + game["app_name"])
                    url = image["url"].replace('"', '')
                    with open('images/' + game["app_name"] + '/' + image["type"] + '.png', 'wb') as f:
                        f.write(requests.get(url).content)
        # Since some games have the background and logo split into two files,
        # we have to do some extra logic to combine those
        if not os.path.isfile('images/' + game["app_name"] + '/FinalArt.png'):
            print('Scaling cover for ' + game["app_name"])
            # First off, check if the extra logo file is even there
            if os.path.isfile('images/' + game["app_name"] + '/DieselGameBoxLogo.png'):
                # Load in the two images that need to be combined
                bg = Image.open('images/' + game["app_name"] + '/DieselGameBoxTall.png')
                # To make sure the background is actually horizontal (3/4) (looking at you Celeste), resize the image
                bg = bg.resize((int(bg.size[1] * 3 / 4), bg.size[1]))
                # Since the logo is transparent, we have to convert it to RGBA
                logo = Image.open('images/' + game["app_name"] + '/DieselGameBoxLogo.png').convert('RGBA')
                # Resize the logo to be ~ 3/4 as wide as the background (EGL does something like this)
                wpercent = ((bg.size[0] * (3 / 4)) / float(logo.size[0]))
                hsize = int((float(logo.size[1]) * float(wpercent)))
                logo = logo.resize((int(bg.size[0] * (3 / 4)), hsize), Image.ANTIALIAS)
                # Calculate where the image has to be placed
                pasteX = int((bg.size[0] - logo.size[0]) / 2)
                pasteY = int((bg.size[1] - logo.size[1]) / 2)
                # And finally copy the background and paste in the image
                finalArt = bg.copy()
                finalArt.paste(logo, (pasteX, pasteY), logo)
                # Write out the file
                finalArt.save('images/' + game["app_name"] + '/FinalArt.png')

                # And we have to do part of that again
                # since the cover for an uninstalled game has the logo half-transparent
                logoCopy = logo.copy()
                logoCopy.putalpha(int(256 * 3 / 4))
                logo.paste(logoCopy, logo)
                uninstalledArt = bg.copy()
                uninstalledArt.paste(logo, (pasteX, pasteY), logo)
                uninstalledArt = uninstalledArt.convert('L')
                uninstalledArt.save('images/' + game["app_name"] + '/UninstalledArt.png')
            # And if the logo and background aren't split
            else:
                # We just open up the background and save that as the final image
                finalArt = Image.open('images/' + game["app_name"] + '/DieselGameBoxTall.png')
                finalArt.save('images/' + game["app_name"] + '/FinalArt.png')
                # And same with the grayscale one
                uninstalledArt = finalArt.convert('L')
                uninstalledArt.save('images/' + game["app_name"] + '/UninstalledArt.png')

    #If the user had to login first, the QApplication will already be running, so we don't have to start it again
    if not loggedIn:
        # Start GUI stuff
        app = QApplication([])
        mainWindow = MainWindow(allGames, installedGames)
        app.exec_()
    else:
        mainWindow = MainWindow(allGames, installedGames)
        mainWindow.show()



def notLoggedIn():
    app = QApplication([])
    window = LoginWindow()
    app.exec_()


if __name__ == '__main__':
    main()
