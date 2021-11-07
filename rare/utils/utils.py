import json
import math
import os
import platform
import shutil
import subprocess
import sys
from logging import getLogger
from typing import Tuple

import requests
from PIL import Image, UnidentifiedImageError
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QRunnable, QSettings
from PyQt5.QtGui import QPalette, QColor, QPixmap

from .models import PathSpec

# Windows

if platform.system() == "Windows":
    from win32com.client import Dispatch  # pylint: disable=E0401

from rare import languages_path, resources_path, image_dir
# Mac not supported

from legendary.core import LegendaryCore

logger = getLogger("Utils")
settings = QSettings("Rare", "Rare")


def download_images(signal: pyqtSignal, core: LegendaryCore):
    if not os.path.isdir(image_dir):
        os.makedirs(image_dir)
        logger.info("Create Image dir")

    # Download Images
    games, dlcs = core.get_game_and_dlc_list()
    dlc_list = []
    for i in dlcs.values():
        dlc_list.append(i[0])

    no_assets = core.get_non_asset_library_items()[0]

    game_list = games + dlc_list + no_assets
    for i, game in enumerate(game_list):
        try:
            download_image(game)
        except json.decoder.JSONDecodeError:
            shutil.rmtree(f"{image_dir}/{game.app_name}")
            download_image(game)
        signal.emit(i / len(game_list) * 100)


def download_image(game, force=False):
    if force and os.path.exists(f"{image_dir}/{game.app_name}"):
        shutil.rmtree(f"{image_dir}/{game.app_name}")
    if not os.path.isdir(f"{image_dir}/" + game.app_name):
        os.mkdir(f"{image_dir}/" + game.app_name)

    # to git picture updates
    if not os.path.isfile(f"{image_dir}/{game.app_name}/image.json"):
        json_data = {"DieselGameBoxTall": None, "DieselGameBoxLogo": None, "Thumbnail": None}
    else:
        json_data = json.load(open(f"{image_dir}/{game.app_name}/image.json", "r"))
    # Download
    download = False
    for image in game.metadata["keyImages"]:
        if image["type"] == "DieselGameBoxTall" or image["type"] == "DieselGameBoxLogo" or image["type"] == "Thumbnail":
            if image["type"] not in json_data.keys():
                json_data[image["type"]] = None
            if json_data[image["type"]] != image["md5"] or not os.path.isfile(
                    f"{image_dir}/{game.app_name}/{image['type']}.png"):
                # Download
                json_data[image["type"]] = image["md5"]
                # os.remove(f"{image_dir}/{game.app_name}/{image['type']}.png")
                json.dump(json_data, open(f"{image_dir}/{game.app_name}/image.json", "w"))
                logger.info(f"Download Image for Game: {game.app_title}")
                url = image["url"]
                with open(f"{image_dir}/{game.app_name}/{image['type']}.png", "wb") as f:
                    f.write(requests.get(url).content)
                    try:
                        img = Image.open(f"{image_dir}/{game.app_name}/{image['type']}.png")
                        img = img.resize((200, int(200 * 4 / 3)))
                        img.save(f"{image_dir}/{game.app_name}/{image['type']}.png")
                        download = True
                    except UnidentifiedImageError as e:
                        logger.warning(e)

    # scale and grey
    uninstalled_image = os.path.join(image_dir, game.app_name + '/UninstalledArt.png')
    if download and os.path.exists(uninstalled_image):
        os.remove(uninstalled_image)
    elif os.path.exists(uninstalled_image):
        return

    if os.path.exists(os.path.join(image_dir, f"{game.app_name}/DieselGameBoxTall.png")):
        # finalArt = Image.open(f'{image_dir}/' + game.app_name + '/DieselGameBoxTall.png')
        # finalArt.save(f'{image_dir}/{game.app_name}/FinalArt.png')
        # And same with the grayscale one
        try:
            bg = Image.open(os.path.join(image_dir, f"{game.app_name}/DieselGameBoxTall.png"))
        except UnidentifiedImageError:
            logger.warning("Reload image for " + game.app_title)
            # avoid endless recursion
            if not force:
                download_image(game, True)
            return
        uninstalledArt = bg.convert('L')
        uninstalledArt = uninstalledArt.resize((200, int(200 * 4 / 3)))
        uninstalledArt.save(f'{image_dir}/{game.app_name}/UninstalledArt.png')

    elif os.path.isfile(f"{image_dir}/{game.app_name}/DieselGameBoxLogo.png"):
        bg: Image.Image = Image.open(f"{image_dir}/{game.app_name}/DieselGameBoxLogo.png")
        bg = bg.resize((int(bg.size[1] * 3 / 4), bg.size[1]))
        logo = Image.open(f'{image_dir}/{game.app_name}/DieselGameBoxLogo.png').convert('RGBA')
        wpercent = ((bg.size[0] * (3 / 4)) / float(logo.size[0]))
        hsize = int((float(logo.size[1]) * float(wpercent)))
        logo = logo.resize((int(bg.size[0] * (3 / 4)), hsize), Image.ANTIALIAS)
        # Calculate where the image has to be placed
        pasteX = int((bg.size[0] - logo.size[0]) / 2)
        pasteY = int((bg.size[1] - logo.size[1]) / 2)
        # And finally copy the background and paste in the image
        # finalArt = bg.copy()
        # finalArt.paste(logo, (pasteX, pasteY), logo)
        # Write out the file
        # finalArt.save(f'{image_dir}/' + game.app_name + '/FinalArt.png')
        logoCopy = logo.copy()
        logoCopy.putalpha(int(256 * 3 / 4))
        logo.paste(logoCopy, logo)
        uninstalledArt = bg.copy()
        uninstalledArt.paste(logo, (pasteX, pasteY), logo)
        uninstalledArt = uninstalledArt.convert('L')
        uninstalledArt.save(f'{image_dir}/' + game.app_name + '/UninstalledArt.png')
    else:
        logger.warning(f"File {image_dir}/{game.app_name}/DieselGameBoxTall.png doesn't exist")


color_role_map = {
    0: "WindowText",
    1: "Button",
    2: "Light",
    3: "Midlight",
    4: "Dark",
    5: "Mid",
    6: "Text",
    7: "BrightText",
    8: "ButtonText",
    9: "Base",
    10: "Window",
    11: "Shadow",
    12: "Highlight",
    13: "HighlightedText",
    14: "Link",
    15: "LinkVisited",
    16: "AlternateBase",
    # 17: "NoRole",
    18: "ToolTipBase",
    19: "ToolTipText",
    20: "PlaceholderText",
    # 21: "NColorRoles",
}

color_group_map = {
    0: "Active",
    1: "Disabled",
    2: "Inactive",
}


def load_color_scheme(path: str):
    palette = QPalette()
    scheme = QSettings(path, QSettings.IniFormat)
    try:
        scheme.beginGroup("ColorScheme")
        for g in color_group_map:
            scheme.beginGroup(color_group_map[g])
            group = QPalette.ColorGroup(g)
            for r in color_role_map:
                role = QPalette.ColorRole(r)
                color = scheme.value(color_role_map[r], None)
                if color is not None:
                    palette.setColor(group, role, QColor(color))
                else:
                    palette.setColor(group, role, palette.color(QPalette.Active, role))
            scheme.endGroup()
        scheme.endGroup()
    except:
        palette = None
    return palette


def get_color_schemes():
    colors = []
    for file in os.listdir(os.path.join(resources_path, "colors")):
        if file.endswith(".scheme") and os.path.isfile(os.path.join(resources_path, "colors", file)):
            colors.append(file.replace(".scheme", ""))
    return colors


def get_style_sheets():
    styles = []
    for folder in os.listdir(os.path.join(resources_path, "stylesheets")):
        if os.path.isfile(os.path.join(resources_path, "stylesheets", folder, "stylesheet.qss")):
            styles.append(folder)
    return styles


def get_translations():
    langs = ["en"]
    for i in os.listdir(languages_path):
        if i.endswith(".qm"):
            langs.append(i.split(".")[0])
    return langs


def get_latest_version():
    try:
        resp = requests.get("https://api.github.com/repos/Dummerle/Rare/releases/latest")
        tag = resp.json()["tag_name"]
        return tag
    except requests.exceptions.ConnectionError:
        return "0.0.0"


def get_size(b: int) -> str:
    for i in ['', 'K', 'M', 'G', 'T', 'P', 'E']:
        if b < 1024:
            return f"{b:.2f}{i}B"
        b /= 1024


def create_rare_desktop_link(type_of_link):
    # Linux
    if platform.system() == "Linux":
        if type_of_link == "desktop":
            path = os.path.expanduser("~/Desktop/")
        elif type_of_link == "start_menu":
            path = os.path.expanduser("~/.local/share/applications/")
        else:
            return

        if p := os.environ.get("APPIMAGE"):
            executable = p
        else:
            executable = f"{sys.executable} {os.path.abspath(sys.argv[0])}"
        with open(os.path.join(path, "Rare.desktop"), "w") as desktop_file:
            desktop_file.write("[Desktop Entry]\n"
                               f"Name=Rare\n"
                               f"Type=Application\n"
                               f"Icon={os.path.join(resources_path, 'images', 'Rare.png')}\n"
                               f"Exec={executable}\n"
                               "Terminal=false\n"
                               "StartupWMClass=rare\n"
                               )
            desktop_file.close()
        os.chmod(os.path.expanduser(os.path.join(path, "Rare.desktop")), 0o755)

    elif platform.system() == "Windows":
        # Target of shortcut
        if type_of_link == "desktop":
            target_folder = os.path.expanduser('~/Desktop/')
        elif type_of_link == "start_menu":
            target_folder = os.path.expandvars("%appdata%/Microsoft/Windows/Start Menu")
        else:
            logger.warning("No valid type of link")
            return
        linkName = "Rare.lnk"

        # Path to location of link file
        pathLink = os.path.join(target_folder, linkName)

        executable = sys.executable
        executable = executable.replace("python.exe", "pythonw.exe")
        logger.debug(executable)
        # Add shortcut
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(pathLink)
        shortcut.Targetpath = executable
        if not sys.executable.endswith("Rare.exe"):
            shortcut.Arguments = os.path.abspath(sys.argv[0])

        # Icon
        shortcut.IconLocation = os.path.join(resources_path, "images", "Rare.ico")

        shortcut.save()


def create_desktop_link(app_name, core: LegendaryCore, type_of_link="desktop") -> bool:
    igame = core.get_installed_game(app_name)

    if os.path.exists(p := os.path.join(image_dir, igame.app_name, 'Thumbnail.png')):
        icon = p
    elif os.path.exists(p := os.path.join(image_dir, igame.app_name, "DieselGameBoxLogo.png")):
        icon = p
    else:
        icon = os.path.join(os.path.join(image_dir, igame.app_name, "DieselGameBoxTall.png"))
    icon = icon.replace(".png", "")

    # Linux
    if platform.system() == "Linux":
        if type_of_link == "desktop":
            path = os.path.expanduser(f"~/Desktop/")
        elif type_of_link == "start_menu":
            path = os.path.expanduser("~/.local/share/applications/")
        else:
            return False
        if not os.path.exists(path):
            return False
        if p := os.environ.get("APPIMAGE"):
            executable = p
        else:
            executable = f"{sys.executable} {os.path.abspath(sys.argv[0])}"
        with open(f"{path}{igame.title}.desktop", "w") as desktop_file:
            desktop_file.write("[Desktop Entry]\n"
                               f"Name={igame.title}\n"
                               f"Type=Application\n"
                               f"Icon={icon}.png\n"
                               f"Exec={executable} launch {app_name}\n"
                               "Terminal=false\n"
                               "StartupWMClass=rare-game\n"
                               )
            desktop_file.close()
        os.chmod(os.path.expanduser(f"{path}{igame.title}.desktop"), 0o755)

    # Windows
    elif platform.system() == "Windows":
        # Target of shortcut
        if type_of_link == "desktop":
            target_folder = os.path.expanduser('~/Desktop/')
        elif type_of_link == "start_menu":
            target_folder = os.path.expandvars("%appdata%/Microsoft/Windows/Start Menu")
        else:
            logger.warning("No valid type of link")
            return False
        if not os.path.exists(target_folder):
            return False

        # Name of link file
        linkName = igame.title
        for c in r'<>?":|\/*':
            linkName.replace(c, "")

        linkName = linkName.strip() + '.lnk'

        # Path to location of link file
        pathLink = os.path.join(target_folder, linkName)

        # Add shortcut
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(pathLink)
        if sys.executable.endswith("Rare.exe"):
            executable = sys.executable
        else:
            executable = f"{sys.executable} {os.path.abspath(sys.argv[0])}"
        shortcut.Targetpath = executable
        shortcut.Arguments = f'launch {app_name}'
        shortcut.WorkingDirectory = os.getcwd()

        # Icon
        if not os.path.exists(icon + ".ico"):
            img = Image.open(icon + ".png")
            img.save(icon + ".ico")
            logger.info("Create Icon")
        shortcut.IconLocation = os.path.join(icon + ".ico")

        shortcut.save()
        return True

    elif platform.system() == "Darwin":
        return False


def get_pixmap(app_name: str) -> QPixmap:
    for img in ["FinalArt.png", "DieselGameBoxTall.png", "DieselGameBoxLogo.png"]:
        if os.path.exists(image := os.path.join(image_dir, app_name, img)):
            pixmap = QPixmap(image)
            break
    else:
        pixmap = QPixmap()
    return pixmap


def get_uninstalled_pixmap(app_name: str) -> QPixmap:
    if os.path.exists(image := os.path.join(image_dir, app_name, "UninstalledArt.png")):
        pixmap = QPixmap(image)
    else:
        pixmap = QPixmap()
    return pixmap


def optimal_text_background(image: list) -> Tuple[int, int, int]:
    """
    Finds an optimal background color for text on the image by calculating the
    average color of the image and inverting it.

    The image list is supposed to be a one-dimensional list of arbitrary length
    containing RGB tuples, ranging from 0 to 255.
    """
    # cursed, I know
    average = map(lambda value: value / len(image), map(sum, zip(*image)))
    inverted = map(lambda value: 255 - value, average)
    return tuple(inverted)


def text_color_for_background(background: Tuple[int, int, int]) -> Tuple[int,
                                                                         int,
                                                                         int]:
    """
    Calculates whether a black or white text color would fit better for the
    given background, and returns that color. This is done by calculating the
    luminance and simple comparing of bounds
    """
    # see https://alienryderflex.com/hsp.html
    (red, green, blue) = background
    luminance = math.sqrt(
        0.299 * red ** 2 +
        0.587 * green ** 2 +
        0.114 * blue ** 2)
    if luminance < 127:
        return 255, 255, 255
    else:
        return 0, 0, 0


class WineResolverSignals(QObject):
    result_ready = pyqtSignal(str)


class WineResolver(QRunnable):

    def __init__(self, path: str, app_name: str, core: LegendaryCore):
        super(WineResolver, self).__init__()
        self.setAutoDelete(True)
        self.signals = WineResolverSignals()
        self.wine_env = os.environ.copy()
        self.wine_env.update(core.get_app_environment(app_name))
        self.wine_env['WINEDLLOVERRIDES'] = 'winemenubuilder=d;mscoree=d;mshtml=d;'
        self.wine_env['DISPLAY'] = ''
        self.wine_binary = core.lgd.config.get(
            app_name, 'wine_executable',
            fallback=core.lgd.config.get('default', 'wine_executable', fallback='wine'))
        self.winepath_binary = os.path.join(os.path.dirname(self.wine_binary), 'winepath')
        self.path = PathSpec(core, app_name).cook(path)

    @pyqtSlot()
    def run(self):
        if 'WINEPREFIX' not in self.wine_env:
            # pylint: disable=E1136
            self.signals.result_ready[str].emit(str())
            return
        path = self.path.strip().replace('/', '\\')
        cmd = 'cd {} & cd'.format(path)
        # [self.wine_binary, 'cmd', '/c', 'echo', path] if path not exists alternative
        proc = subprocess.Popen([self.wine_binary, 'cmd', '/c', cmd],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=self.wine_env, shell=False, text=True)
        out, err = proc.communicate()
        # Clean wine output
        out = out.strip().strip('"')
        proc = subprocess.Popen([self.winepath_binary, '-u', out],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=self.wine_env, shell=False, text=True)
        out, err = proc.communicate()
        real_path = os.path.realpath(out.strip())
        # pylint: disable=E1136
        self.signals.result_ready[str].emit(real_path)
        return
