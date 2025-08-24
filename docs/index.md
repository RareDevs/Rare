<div align="center">
    <img src="https://github.com/RareDevs/Rare/blob/main/docs/assets/RareLogoWide.png?raw=true" alt="Logo" width="200"/>
    <h2>Rare</h2>
    <p>Logo by <a href="https://github.com/MultisampledNight">@MultisampledNight</a> available
        <a href="https://github.com/RareDevs/Rare/blob/main/docs/assets/">here</a>,
        licensed under CC BY-SA 4.0</p>
    <a href="https://discord.gg/YvmABK9YSk" target="_blank">
  <img src="https://discordapp.com/api/guilds/826881530310819914/widget.png?style=shield" alt="Discord Shield">
</a>
</div>


## What is Rare?
A graphical interface for Legendary, a command line alternative to Epic Games launcher, written in PySide6


## Why Rare?
- Runs natively, and supports most of the major platforms
- Gets out of your way when you don't need it, allowing you to enjoy your games
- Tries to be as lightweight as we can make it while still offering a feature-full experience
- Integrates seamlessly with legendary as both projects are developed in Python
- Packages, packages everywhere


## Screenshots

| Game covers                                   | Vertical list                                 |
|-----------------------------------------------|-----------------------------------------------|
| ![alt text](/Rare/assets/RareLibraryIcon.png) | ![alt text](/Rare/assets/RareLibraryList.png) |

| Game details                               | Game settings                                  |
|--------------------------------------------|------------------------------------------------|
| ![alt text](/Rare/assets/RareGameInfo.png) | ![alt text](/Rare/assets/RareGameSettings.png) |

| Downloads                                   | Application settings                       |
|---------------------------------------------|--------------------------------------------|
| ![alt text](/Rare/assets/RareDownloads.png) | ![alt text](/Rare/assets/RareSettings.png) |


## Installation
### Windows
There is an `.msi` installer available in [releases page](https://github.com/RareDevs/Rare/releases).

There is also a semi-portable `.zip` archive in [releases page](https://github.com/RareDevs/Rare/releases) that lets you run Rare without installing it.

**Important**: On recent version of Windows you should have MSVC 2015 installed, you can get it from [here](https://learn.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-studio-2015-2017-2019-and-2022)

#### Packages
- Rare is available as a [Winget package](https://github.com/microsoft/winget-pkgs/tree/master/manifests/d/Dummerle/Rare). You can install Rare with the following one-liner:
    ```lang-default
    winget install rare
    ```

- Rare is available as a [Chocolatey package](https://community.chocolatey.org/packages/rare). You can install Rare with the following one-liner:
    ```lang-default
    choco install rare
    ```

### Linux
### AppImage

Available in [releases page](https://github.com/RareDevs/Rare/releases).

#### Flatpak
Rare is available as a flatpak. See [rare](https://flathub.org/apps/details/io.github.dummerle.rare).

Install it via:
```sh
flatpak install flathub io.github.dummerle.rare
```

Run it via:
```sh
flatpak run io.github.dummerle.rare
```

Alternatively, you can download the flatpak package from [our repository](https://github.com/RareDevs/io.github.dummerle.rare/releases)

#### Arch based
There are some AUR packages available:

- [rare](https://aur.archlinux.org/packages/rare) - for stable releases
- [rare-git](https://aur.archlinux.org/packages/rare-git) - for the latest development version

### macOS
There is a `.dmg` file available in [releases page](https://github.com/RareDevs/Rare/releases).

Rare's macOS binaries are currently not singed and because of that  when you launch Rare, you will see an error,
that the package is from an unknown source. You have to enable it manually in `Settings -> Security and Privacy`.
Otherwise, Gatekeeper will block Rare from running.

After installing Rare, if macOS complains that it is damaged, open a terminal and run the following command
```shell
sudo xattr -dr com.apple.quarantine /Applications/Rare.app
```
which will allow the application to run normally.

Alternatively, you can install using `pip`/`pipx` or from source.


### Latest development version
In the [actions](https://github.com/RareDevs/Rare/actions/workflows/snapshot.yml) tab you can find packages for the latest commits.

**Note**: They might be unstable and likely broken.


### Installation via pip (platform independent)
Execute `pip install Rare` for all users, or `pip install Rare --user` for the current user only.

- Linux, macOS and FreeBSD: execute `rare` in your terminal.
- Windows: execute `pythonw -m rare` in cmd

It is possible to create a desktop link, or a start menu link. Execute the command above with `--desktop-shortcut` or
`--startmenu-shortcut` option, alternatively you can create them in the settings.

**Note about $PATH**:
Depending on your operating system and the `python` distribution, the following paths might need to be in your
environment's `PATH`

| OS      | Path                                       |
|---------|--------------------------------------------|
| Windows | `<python_installation_folder>\Scripts`     |
| Linux   | `/home/<username>/.local/bin`              |
| macOS   | `/Users/<username>/Library/Python/3.x/bin` |


### Run from source
1. Clone the repo: `git clone https://github.com/RareDevs/Rare`.
2. Change your working directory to the project folder: `cd Rare`.
3. Run `pip install -r misc/requirements.in` to install all required dependencies.
4. Run `./tools/ui2py.sh --force`, `./tools/qrc2py.sh --force` and `./tools/ts2qm.py` to prepare the UI components.
5. Finally, run `pip install .`.
6. Run the application with `python3 -m rare`.

#### In Arch Linux
You can run `sudo pacman --needed -S python-wheel python-setuptools python-setuptools-scm python-pyside6 python-qtawesome python-requests python-orjson` and `yay -S legendary python-vdf`.

#### For packaging 
For build and install the package manually, run `python setup.py bdist_wheel` and `python -m installer dist/*.whl`.


## Contributing
There are several options to contribute.

- If you know Python and PyQt, you can implement new features (Some ideas are in the projects tab).
- You can translate the application in your language: Check our [transifex](https://www.transifex.com/rare-1/rare) page for that.

More information is available in CONTRIBUTING.md.


## Reporting issues
If you run into any issues, you can report them by creating an issue on GitHub:
https://github.com/RareDevs/Rare/issues/new/choose

When reporting issues, it is helpful to also include the logs with your issue.
You can find the longs in the following locations depending on your operating system

| OS      | Path                                                     |
|---------|----------------------------------------------------------|
| Windows | `C:\Users\<username>\AppData\Local\Rare\Rare\cache\logs` |
| Linux   | `/home/<username>/.cache/Rare/Rare/logs`                 |
| macOS   | `/Users/<username>/Library/Caches/Rare/Rare/logs`        |

In these folders you will find files named like below

- `Rare_23-12-19--11-14.log`

These are the logs for the main Rare application. As such are importand when Rare itself is crashing.

- `RareLauncher_f4e0c1dff48749fa9145c1585699e276_23-12-17--19-53.log`

These are the logs for each of the games you run through Rare. Rare uses a separate instance of itself
to launch games, and these are the logs of that instance.

If you don't have a GitHub account or you just want to chat, you also can contact us on Discord:
https://discord.gg/YvmABK9YSk


## Common issues
* If you are using multiple accounts, there is a chance that at some point you will not be able to log in into your account and see something like the following.
  > Login failed. Decryption of EPIC launcher user information failed.

  In that case navigate to one of the following directorories depending on your operating system and delete `user.json`

  | OS      | Path                               |
  |---------|------------------------------------|
  | Windows | `%USERPROFILE%\.config\legendary\` |
  | Linux   | `$HOME/.config/legendary/`         |
  | macOS   | `$HOME/.config/legendary/`         |

