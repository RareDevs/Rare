# Rare

## A frontend for legendary, the open source Epic Games Launcher alternative

Rare is a GUI for Legendary, a command line alternative to Epic Games launcher. If you run into an issue, please report
it by creating an issue on GitHub or on Discord: https://discord.gg/YvmABK9YSk

![Discord Shield](https://discordapp.com/api/guilds/826881530310819914/widget.png?style=shield)

## Installation

### Installation via pip (recommend)

Execute `pip install Rare` for all users Or `pip install Rare --user` for only one user.

Linux: execute `rare` in your terminal.

Windows: execute `pythonw -m rare` in cmd

It is possible to create a desktop link, or a start menu link. Execute the command above with `--desktop-shortcut`
or `--startmenu-shortcut` option

**Note**: On Linux must be `/home/user/.local/bin` in PATH and on Windows must be `PythonInstallationDirectory\Scripts`
in PATH.

### Linux

#### Arch based

There are some AUR packages available:

- [rare](https://aur.archlinux.org/packages/rare) - for stable releases
- [rare-git](https://aur.archlinux.org/packages/rare-git) - for the latest features, which are not in a stable release

#### Other

Install via `pip`.

### Packages

In [releases page](https://github.com/Dummerle/Rare/releases) are AppImages for Linux and a msi file for windows
available

### Run from source

1. Run `pip install -r requirements.txt` to get dependencies. If you use `pacman` you can
   run `sudo pacman --needed -S python-wheel python-setuptools python-pyqt5 python-qtawesome python-requests python-pillow`
2. For unix operating systems run `sh start.sh`. For windows run `set PYTHONPATH=%CD% && python rare`

## Why Rare?

- Rare only uses ~50MB of RAM which is much less than the electron
  based [HeroicGamesLauncher](https://github.com/Heroic-Games-Launcher/HeroicGamesLauncher) uses.
- Rare supports all major platforms (Windows, Linux, Mac) unlike the alternatives.

## Features

- Launch, install and uninstall games
- Authentication(Import from existing installation or via Browser)
- Download progress bar and queue
- Settings (Legendary and games)
- Sync Cloud Saves
- Translations (English, German and French)
- Create desktop shortcut for each game (Note: not supported on Mac yet)
- Display rating from [ProtonDB](https://www.protondb.com/) for each game

## Planned Features

- More Translations (Need help)
- More Information about Games More planned features are in [projects](https://github.com/Dummerle/Rare/projects/1)

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
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/Settings.png?raw=true)
