# Rare

## A frontend for legendary, the open source Epic Games Launcher alternative

Rare is a GUI for Legendary, a command line aternative to Epic Games launcher. 
It is currently considered beta software. You will probably run into issues, so it is
recommend to make a backup. If you run into an issue, please report it by creating an issue on github or on Discord: https://discord.gg/YvmABK9YSk 

![Discord Shield](https://discordapp.com/api/guilds/826881530310819914/widget.png?style=shield)

## Installation

### Installation via pip (recommend)

Execute `pip install Rare` for all users Or `pip install Rare --user` for only one user. Then execute `rare` in your terminal or cmd

**Note**: On Linux must be `/home/user/.local/bin` in PATH and on Windows must be `PythonInstallationDirectory\Scripts` in PATH. 

### Windows Simple

Download Rare.exe from the [releases page](https://github.com/Dummerle/Rare/releases) and execute it. 

**Note:**
Using the exe file could cause errors with Windows Defender or other Anti Virus. Sometimes it is not possible to download games and sometimes the app crashes. In this case please use pip

### Linux

#### Arch based

There are some AUR packages available:
 - [rare](https://aur.archlinux.org/packages/rare) - for stable releases
 - [rare-git](https://aur.archlinux.org/packages/rare-git) - for the latest features, which are not in a stable release

#### Debian based

There is a `.deb` package available from the [releases page](https://github.com/Dummerle/Rare/releases): `sudo dpkg –i Rare.deb`

#### Other

Install via `pip`.

## Run from source
1. Run `pip install -r requirements.txt` to get dependencies. If you use `pacman` you can run `sudo pacman --needed -S python-wheel python-setuptools python-pyqt5 python-qtawesome python-requests python-pillow`
2. For unix operating systems run `sh start.sh`. For windows run `set PYTHONPATH=%CD% && python Rare`

## Why Rare?

- Rare uses much less RAM than electron based apps such as [HeroicGL](https://github.com/Heroic-Games-Launcher/HeroicGamesLauncher) and EpicGL which allows the games to run better.
- Rare supports all major platforms (Windows, Linux, macOS) unlike the alternatives.

## Features

- Launch, install and uninstall games
- Authentication(Import from existing installation and via Browser)
- Download progress bar, queue
- Settings (Legendary and games)
- Sync Cloud Saves
- Translations (English, German and French)

## Planned Features
- More Translations (Need help)
- More Information about Games
More planned features are in projects

## Contributing
There are more options to contribute. 
- If you can Python and PyQt you can implement new Features (Some ideas are in Projects).
- If you are a designer, you can add Stylesheets or create a logo or a banner
- You can translate the application in your language

More Information is in CONTRIBUTING.md

## Images

![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/Rare.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/GameInfo.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/RareSettings.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/RareDownloads.png?raw=true)
