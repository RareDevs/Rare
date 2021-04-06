# Rare

## A frontend for legendary, the open source Epic Games Launcher alternative

Rare is a GUI for Legendary, a command line aternative to Epic Games launcher. 
It is currently considered beta software. You will probably run into issues, so it is
recommend to make a backup. If you run into an issue, please report it by creating an issue on github or on Discord: https://discord.gg/YvmABK9YSk 

![Discord Shield](https://discordapp.com/api/guilds/826881530310819914/widget.png?style=shield)

## Installation

### Installation via pip (recommend)

Execute `pip install Rare` for all users Or `pip install Rare --user` for only one user

**Note**: On Linux must be /home/user/.local/bin in PATH

### Windows Simple

Download Rare.exe from the [releases page](https://github.com/Dummerle/Rare/releases) and place it somewhere in PATH

**Note**
Using the exe file could cause errors

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

Rare uses much less RAM than electron based apps such as [HeroicGL](https://github.com/Heroic-Games-Launcher/HeroicGamesLauncher) and EpicGL which allows the games to run better.
Rare supports all major platforms (Windows, Linux, MacOS) unlike the alternatives.

## Features

- Launch, install and uninstall games
- Authentication(Import from existing installation and via Browser)
- Download progress bar
- Settings (Legendary and games)
- Sync Cloud Saves
- Translations (English and German)

## Planned Features
- Offline mode
- More Translations (Need help)
- More Information about Games
More planned features are in projects

## Contributing
There are more options to contribute. 
- If you can Python and PyQt you can implement new Features.
- If you are a designer, you can add Stylesheets or create a logo or a banner
- You can translate the application

More Information is in CONTRIBUTING.md

## Images

![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/Rare.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/GameInfo.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/RareSettings.png?raw=true)

