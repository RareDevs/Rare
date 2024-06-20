import os
from enum import IntEnum
from logging import getLogger
from typing import Union, Type, Dict, Tuple, Iterable

import qtawesome
from PySide6.QtCore import (
    QObject,
    QSettings,
    QFile,
    Qt,
    QLocale,
    QDirIterator,
)
from PySide6.QtGui import QPalette, QColor, QFontMetrics
from PySide6.QtWidgets import QApplication, QStyleFactory, QLabel
from shiboken6.Shiboken import Object as ShibokenObject

from rare.utils.paths import resources_path

logger = getLogger("Utils")


class ExitCodes(IntEnum):
    EXIT = 0
    LOGOUT = -133742


color_role_map: Dict[int, str] = {
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

color_group_map: Dict[int, str] = {
    0: "Active",
    1: "Disabled",
    2: "Inactive",
}


def load_color_scheme(path: str) -> QPalette:
    palette = QPalette()
    scheme = QSettings(path, QSettings.Format.IniFormat)
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
                    palette.setColor(group, role, palette.color(QPalette.ColorGroup.Active, role))
            scheme.endGroup()
        scheme.endGroup()
    except:
        palette = None
    return palette


def get_static_style() -> str:
    file = QFile(":/static_css/stylesheet.qss")
    file.open(QFile.OpenModeFlag.ReadOnly)
    static = file.readAll().data().decode("utf-8")
    file.close()
    return static


def set_color_pallete(color_scheme: str) -> None:
    static = get_static_style()
    qApp: QApplication = QApplication.instance()

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
        icon_color_normal = qApp.palette().color(QPalette.ColorRole.WindowText).name()
        icon_color_disabled = qApp.palette().color(QPalette.ColorRole.WindowText).name()
        qtawesome.set_defaults(color=icon_color_normal, color_disabled=icon_color_disabled)


def get_color_schemes() -> Iterable[str]:
    it = QDirIterator(":/schemes/")
    while it.hasNext():
        it.next()
        yield it.fileName()


def set_style_sheet(style_sheet: str) -> None:
    static = get_static_style()
    qApp: QApplication = QApplication.instance()

    if not style_sheet:
        qApp.setStyle(QStyleFactory.create(qApp.property("rareDefaultQtStyle")))
        qApp.setStyleSheet(static)
        return

    qApp.setStyle(QStyleFactory.create("Fusion"))
    file = QFile(f":/stylesheets/{style_sheet}/stylesheet.qss")
    file.open(QFile.OpenModeFlag.ReadOnly)
    stylesheet = file.readAll().data().decode("utf-8")
    file.close()
    qApp.setStyleSheet(stylesheet + static)

    icon_color_normal = qApp.palette().color(QPalette.ColorRole.Text).name()
    icon_color_disabled = qApp.palette().color(QPalette.ColorRole.Text).name()
    qtawesome.set_defaults(color="#eee", color_disabled="#eee")


def get_style_sheets() -> Iterable[str]:
    it = QDirIterator(":/stylesheets/")
    while it.hasNext():
        it.next()
        yield it.fileName()


def get_translations() -> Tuple[Tuple[str, str], ...]:
    langs = []
    for i in os.listdir(os.path.join(resources_path, "languages")):
        if i.endswith(".qm") and i.startswith("rare_"):
            locale = QLocale(i.removesuffix(".qm").removeprefix("rare_"))
            langs.append((locale.name(), f"{locale.nativeLanguageName()} ({locale.nativeCountryName()})"))
    return tuple(langs)


def path_size(path: Union[str, os.PathLike]) -> int:
    return sum(
        os.stat(os.path.join(dp, f)).st_size
        for dp, dn, filenames in os.walk(path)
        for f in filenames
        if os.path.isfile(os.path.join(dp, f))
    )


def format_size(b: Union[int, float]) -> str:
    for s in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei"):
        if b < 1024:
            return f"{b:.2f} {s}B"
        b /= 1024


def qta_icon(icn_str: str, fallback: str = None, **kwargs):
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


def widget_object_name(widget: Union[QObject, ShibokenObject, Type], suffix: str) -> str:
    suffix = f"_{suffix}" if suffix else ""
    if isinstance(widget, QObject):
        return f"{type(widget).__name__}{suffix}"
    elif isinstance(widget, ShibokenObject) or isinstance(widget, type):
        return f"{widget.__name__}{suffix}"
    else:
        raise RuntimeError(f"Argument {widget} not a QObject or type of QObject")


def elide_text(label: QLabel, text: str) -> str:
    metrics = QFontMetrics(label.font())
    return metrics.elidedText(text, Qt.TextElideMode.ElideRight, label.sizeHint().width())


def style_hyperlink(link: str, title: str) -> str:
    return "<a href='{}' style='color: #2980b9; text-decoration:none'>{}</a>".format(link, title)
