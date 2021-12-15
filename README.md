# Rare
[![Discord Shield](https://discordapp.com/api/guilds/826881530310819914/widget.png?style=shield)](https://discord.gg/YvmABK9YSk)

## A frontend for legendary, the open source Epic Games Launcher alternative

Rare is a graphical interface for Legendary, a command line alternative to Epic Games launcher, based on PyQt5

<div align="center">
    <img src="https://github.com/Dummerle/Rare/blob/main/rare/resources/images/Rare_nonsquared.png?raw=true" alt="Logo" width="200"/>
    <p><i>Logo by <a href="https://github.com/MultisampledNight">@MultisampledNight</a> available
        <a href="https://github.com/Dummerle/Rare/blob/main/rare/resources/images/">here</a>,
        licensed under CC BY-SA 4.0</i></p>
</div>

## Installation

### Installation via pip (recommend)

Execute `pip install Rare` for all users, or `pip install Rare --user` for the current user only.

To install latest git version use `pip install --upgrade https://github.com/Dummerle/Rare/archive/refs/heads/main.zip`.

Linux and Mac: execute `rare` in your terminal.

Windows: execute `pythonw -m rare` in cmd

It is possible to create a desktop link, or a start menu link. Execute the command above with `--desktop-shortcut`
or `--startmenu-shortcut` option, alternatively you can create them in the settings.

**Note**: On Linux must be `/home/user/.local/bin` in PATH and on Windows must be `PythonInstallationDirectory\Scripts`
in PATH. On Mac is the Path `/Users/user/Library/Python/3.x/bin`.

### Linux

#### Arch based

There are some AUR packages available:

- [rare](https://aur.archlinux.org/packages/rare) - for stable releases
- [rare-git](https://aur.archlinux.org/packages/rare-git) - for the latest features, which are not in a stable release

#### Debian based

- DUR package: [rare](https://mpr.hunterwittenborn.com/packages/rare)
- .deb file in [releases page](https://github.com/Dummerle/Rare/releases)

#### Other

Install via `pip` or use the AppImage.

### macOS

There is a .dmg file available in [releases page](https://github.com/Dummerle/Rare/releases).

**Note**: You have to enable it manually in `Settings -> Security and Privacy`. Otherwise, Gatekeeper will block Rare
from running.

You can also use `pip`.

### Packages

In [releases page](https://github.com/Dummerle/Rare/releases) are AppImages for Linux, a .msi file for windows and a .dmg
file for macOS available

### Latest packages

In the [actions](https://github.com/Dummerle/Rare/actions) tab you can find packages for the latest commits.

**Note**: They might be unstable.

### Run from source

1. Clone the repo with Submodule: `git clone https://github.com/Dummerle/Rare --recurse-submodules`.
2. Change your working directory to the project folder: `cd Rare`
3. Run `pip install -r requirements.txt` to install all required dependencies. If you are on Arch you can
   run `sudo pacman --needed -S python-wheel python-setuptools python-pyqt5 python-qtawesome python-requests python-pillow`
3. Run `python3 -m rare`

## Why Rare?

- Rare only uses ~50MB of RAM which is much less than the electron
  based [HeroicGamesLauncher](https://github.com/Heroic-Games-Launcher/HeroicGamesLauncher) uses.
- Rare supports most major platforms (Windows, Linux, Mac) unlike the alternatives.

## Issues

If you run into any issues, please report it by creating an issue on GitHub or on Discord: https://discord.gg/YvmABK9YSk

## Contributing

There are several options to contribute.

- If you can Python and PyQt you can implement new Features (Some ideas are in Projects).
- If you are a designer, you can add Stylesheets or create a logo or a banner.
- You can translate the application in your language: Check our [transifex](https://www.transifex.com/rare-1/rare) page
  for that.

More information is available in CONTRIBUTING.md.

## Images

![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/Rare.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/GameInfo.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/RareSettings.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/RareDownloads.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/GameSettings.png?raw=true)
