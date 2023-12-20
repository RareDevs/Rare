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


## Why Rare?

- Runs natively, and supports most of the major platforms
- Gets out of your way when you don't need it, allowing you to enjoy your games
- Tries to be as lightweight as we can make it while still offering a feature-full experience
- Integrates seamlessly with legendary as both projects are developed in Python
- Packages, packages everywhere


## Reporing issues

If you run into any issues, you can report them by creating an issue on GitHub: https://github.com/RareDevs/Rare/issues/new/choose

When reporting issues, it is helpful to also include the logs with your issue.
You can find the longs in the following locations depending on your operating system

| OS      | Path                                                     |
|---------|----------------------------------------------------------|
| Windows | `C:\Users\<username>\AppData\Local\Rare\Rare\cache\logs` |
| Linux   | `/home/<username>/.cache/Rare/Rare/logs`                 |
| masOS   | `/Users/<username>/Library/Caches/Rare/Rare/logs`        |

In these folders you will find files named like below

- `Rare_23-12-19--11-14.log`

These are the logs for the main Rare application. As such are importand when Rare itself is crashing.
 
- `RareLauncher_f4e0c1dff48749fa9145c1585699e276_23-12-17--19-53.log`

These are the logs for each of the games you run through Rare. Rare uses a separate instance of itself
to launch games, and these are the logs of that instance.

If you don't have a GitHub account or you just want to chat, you also can contact us on Discord: https://discord.gg/YvmABK9YSk


## Installation

### Linux

#### Flatpak

Rare is available as a flatpak. See [rare](https://flathub.org/apps/details/io.github.dummerle.rare).

Install it via:

`flatpak install flathub io.github.dummerle.rare`

Run it via:

`flatpak run io.github.dummerle.rare`

#### Arch based

There are some AUR packages available:

- [rare](https://aur.archlinux.org/packages/rare) - for stable releases
- [rare-git](https://aur.archlinux.org/packages/rare-git) - for the latest development version

#### Debian based

- DUR package: [rare](https://mpr.hunterwittenborn.com/packages/rare)
- `.deb` file in [releases page](https://github.com/Dummerle/Rare/releases)

**Note**:
- pypresence is an optional package. You can install it from [DUR](https://mpr.hunterwittenborn.com/packages/python3-pypresence) or with pip.
- Some icons might look strange on Debian based distributions. The official python3-qtawesome package is too old.


### macOS

There is a `.dmg` file available in [releases page](https://github.com/Dummerle/Rare/releases).

**Note**: When you launch it, you will see an error, that the package is from an unknown source. You have to enable it  manually in `Settings -> Security and Privacy`. Otherwise, Gatekeeper will block Rare from running.

You can also use `pip`.


### Windows

There is an `.msi` installer available in [releases page](https://github.com/Dummerle/Rare/releases).

There is also a semi-portable `.zip` archive in [releases page](https://github.com/Dummerle/Rare/releases) that lets you run Rare without installing it.

**Important**: On recent version of Windows you should have MSVC 2015 installed, you can get it from [here](https://learn.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-studio-2015-2017-2019-and-2022)

#### Packages

- Rare is available as a [Winget package](https://github.com/microsoft/winget-pkgs/tree/master/manifests/d/Dummerle/Rare)
You can install Rare with the following one-liner:

    `winget install rare`

- Rare is available as a [Chocolatey package](https://community.chocolatey.org/packages/rare).
You can install Rare with the following one-liner:

    `choco install rare`

- We also have a beta tool for Windows: [Rare Updater](https://github.com/Dummerle/RareUpdater), which installs and updates rare with a single click

### Packages

In [releases page](https://github.com/Dummerle/Rare/releases), AppImages are available for Linux, a .msi file for windows and a .dmg
file for macOS.

### Latest development version

In the [actions](https://github.com/Dummerle/Rare/actions) tab you can find packages for the latest commits.

**Note**: They might be unstable and likely broken.


### Installation via pip (platform independent)

Execute `pip install Rare` for all users, or `pip install Rare --user` for the current user only.

- Linux, macOS and FreeBSD: execute `rare` in your terminal.
- Windows: execute `pythonw -m rare` in cmd

It is possible to create a desktop link, or a start menu link. Execute the command above with `--desktop-shortcut` or `--startmenu-shortcut` option, alternatively you can create them in the settings.

**Note about $PATH**:
Depending on your operating system and the `python` distribution, the following paths might need to be in your environment's `PATH`

| OS      | Path                                       |
|---------|--------------------------------------------|
| Windows | `<python_installation_folder>\Scripts`     |
| Linux   | `/home/<username>/.local/bin`              |
| masOS   | `/Users/<username>/Library/Python/3.x/bin` |


### Run from source

1. Clone the repo: `git clone https://github.com/Dummerle/Rare
2. Change your working directory to the project folder: `cd Rare`
3. Run `pip install -r requirements.txt` to install all required dependencies.
   * If you want to be able to use the automatic login and Discord pypresence, run `pip install -r requirements-full.txt`
   * If you are on Arch you can run `sudo pacman --needed -S python-wheel python-setuptools python-pyqt5 python-qtawesome python-requests python-orjson` and `yay -S legendary`
   * If you are on FreeBSD you have to install py39-qt5 from the packages: `sudo pkg install py39-qt5`
4. Run `python3 -m rare`


## Contributing

There are several options to contribute.

- If you know Python and PyQt, you can implement new features (Some ideas are in the projects tab).
- You can translate the application in your language: Check our [transifex](https://www.transifex.com/rare-1/rare) page for that.

More information is available in CONTRIBUTING.md.

## Images

![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/Rare.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/GameInfo.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/RareSettings.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/RareDownloads.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/main/Screenshots/GameSettings.png?raw=true)
