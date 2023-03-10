import os
from logging import getLogger
from typing import List, Union, Type

import qtawesome
import requests
from PyQt5.QtCore import (
    pyqtSignal,
    QObject,
    QRunnable,
    QSettings,
    QFile,
    QDir,
    Qt,
)
from PyQt5.QtGui import QPalette, QColor, QFontMetrics
from PyQt5.QtWidgets import qApp, QStyleFactory, QLabel
from PyQt5.sip import wrappertype
from legendary.core import LegendaryCore
from requests.exceptions import HTTPError

from rare.utils.paths import resources_path

logger = getLogger("Utils")
settings = QSettings("Rare", "Rare")

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


def load_color_scheme(path: str) -> QPalette:
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


def get_static_style() -> str:
    file = QFile(":/static_css/stylesheet.qss")
    file.open(QFile.ReadOnly)
    static = file.readAll().data().decode("utf-8")
    file.close()
    return static


def set_color_pallete(color_scheme: str) -> None:
    static = get_static_style()

    if not color_scheme:
        qApp.setStyle(QStyleFactory.create(qApp.property("rareDefaultQtStyle")))
        qApp.setPalette(qApp.style().standardPalette())
        qApp.setStyleSheet(static)
        return

    qApp.setStyle(QStyleFactory.create("Fusion"))
    custom_palette = load_color_scheme(f":/schemes/{color_scheme}")
    if custom_palette is not None:
        qApp.setPalette(custom_palette)
        qApp.setStyleSheet(static)
        icon_color = qApp.palette().color(QPalette.Foreground).name()
        qtawesome.set_defaults(color=icon_color)


def get_color_schemes() -> List[str]:
    colors = []
    for file in QDir(":/schemes"):
        colors.append(file)
    return colors


def set_style_sheet(style_sheet: str) -> None:
    static = get_static_style()

    if not style_sheet:
        qApp.setStyle(QStyleFactory.create(qApp.property("rareDefaultQtStyle")))
        qApp.setStyleSheet(static)
        return

    qApp.setStyle(QStyleFactory.create("Fusion"))
    file = QFile(f":/stylesheets/{style_sheet}/stylesheet.qss")
    file.open(QFile.ReadOnly)
    stylesheet = file.readAll().data().decode("utf-8")
    file.close()
    qApp.setStyleSheet(stylesheet + static)

    icon_color = qApp.palette().color(QPalette.Text).name()
    qtawesome.set_defaults(color="#eeeeee")


def get_style_sheets() -> List[str]:
    styles = []
    for file in QDir(":/stylesheets/"):
        styles.append(file)
    return styles


def get_translations():
    langs = ["en"]
    for i in os.listdir(os.path.join(resources_path, "languages")):
        if i.endswith(".qm") and not i.startswith("qt_"):
            langs.append(i.split(".")[0])
    return langs


def get_latest_version():
    try:
        resp = requests.get(
            "https://api.github.com/repos/Dummerle/Rare/releases/latest", timeout=2,
        )
        tag = resp.json()["tag_name"]
        return tag
    except requests.exceptions.ConnectionError:
        return "0.0.0"


def path_size(path: Union[str, os.PathLike]) -> int:
    return sum(
        os.stat(os.path.join(dp, f)).st_size
        for dp, dn, filenames in os.walk(path)
        for f in filenames if os.path.isfile(os.path.join(dp,f ))
    )


def format_size(b: Union[int, float]) -> str:
    for s in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei"]:
        if b < 1024:
            return f"{b:.2f} {s}B"
        b /= 1024


class CloudWorker(QRunnable):
    class Signals(QObject):
        # List[SaveGameFile]
        result_ready = pyqtSignal(dict)

    def __init__(self, core: LegendaryCore):
        super(CloudWorker, self).__init__()
        self.core = core
        self.signals = CloudWorker.Signals()
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            saves = self.core.get_save_games()
        except HTTPError:
            self.signals.result_ready.emit(None)
            return

        save_games = set()
        for igame in self.core.get_installed_list():
            game = self.core.get_game(igame.app_name)
            if self.core.is_installed(igame.app_name) and game.supports_cloud_saves:
                save_games.add(igame.app_name)

        latest_saves = dict()
        for s in sorted(saves, key=lambda a: a.datetime):
            if s.app_name in save_games:
                if not latest_saves.get(s.app_name):
                    latest_saves[s.app_name] = []
                latest_saves[s.app_name].append(s)

        self.signals.result_ready.emit(latest_saves)


def icon(icn_str: str, fallback: str = None, **kwargs):
    try:
        return qtawesome.icon(icn_str, **kwargs)
    except Exception as e:
        if not fallback:
            logger.warning(f"{e} {icn_str}")
    if fallback:
        try:
            return qtawesome.icon(fallback, **kwargs)
        except Exception as e:
            logger.error(str(e))
    if kwargs.get("color"):
        kwargs["color"] = "red"
    return qtawesome.icon("ei.error", **kwargs)


def widget_object_name(widget: Union[QObject,wrappertype,Type], suffix: str) -> str:
    suffix = f"_{suffix}" if suffix else ""
    if isinstance(widget, QObject):
        return f"{type(widget).__name__}{suffix}"
    elif isinstance(widget, wrappertype) or isinstance(widget, type):
        return f"{widget.__name__}{suffix}"
    else:
        raise RuntimeError(f"Argument {widget} not a QObject or type of QObject")


def elide_text(label: QLabel, text: str) -> str:
    metrics = QFontMetrics(label.font())
    return metrics.elidedText(text, Qt.ElideRight, label.sizeHint().width())
