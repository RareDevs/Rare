# Rare

## A frontend for legendary, the open source Epic Games Launcher alternative

Rare is currently considered beta software and in no way feature-complete. You will probably run into issues, so it is recommend to make a backup. If you have features you want to have in this app, create an issue on github, contact me on Discord (Dummerle#7419) or build it yourself. Please report bugs so I can fix them.

## Installation

### Installation via pip (recommend)

Execute `pip install Rare` for all users Or `pip install Rare --user` for only one user

### Windows Simple

Download Rare.exe from the [releases page](https://github.com/Dummerle/Rare/releases) and place it somewhere in PATH

**Note**
Using the exe-file could cause an error with the stylesheets

### Linux

#### Arch based

There are some AUR packages available:
 - [rare](https://aur.archlinux.org/packages/rare)
 - [rare-git](https://aur.archlinux.org/packages/rare-git)

#### Debian based

There is a `.deb` package available from the [releases page](https://github.com/Dummerle/Rare/releases): `sudo dpkg –i Rare.deb`

#### Other

Install via `pip`.

## Run from source
1. Run `pip install -r requirements.txt` to get dependencies. If you use `pacman` you can run `sudo pacman --needed -S python-wheel python-setuptools python-pyqt5 python-qtawesome python-requests python-pillow`
2. For unix operating systems run `sh start.sh`. For windows run `set PYTHONPATH=%CD% && python Rare`

## Why Rare?

Rare uses much less RAM than electron based apps such as [HeroicGL](https://github.com/Heroic-Games-Launcher/HeroicGamesLauncher) and EpicGL which allows the games to run better. Rare supports all major platforms (Windows, Linux, MacOS) unlike the alternatives.

## Implemented

- Launch, install and uninstall games
- Authentication(Import from existing installation and via Browser)
- Download progress bar
- Settings (Legendary and games)
- Translations (English and German)

## Planned
- Sync Cloud Saves
- Offline mode
- More Translations

## Images

![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/Rare.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/GameInfo.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/RareSettings.png?raw=true)

