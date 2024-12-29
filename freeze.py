from cx_Freeze import setup, Executable

from rare import __version__ as _version

_name = "Rare"
_author = "RareDevs"
_description = "Open source alternative for Epic Games Launcher, using Legendary"

_icon = "rare/resources/images/Rare"
_license = "LICENSE"

build_exe_options = {
    "bin_excludes": [ "qpdf.dll", "libqpdf.so", "libqpdf.dylib"],
    "excludes": [
        "tkinter",
        "unittest",
        "pydoc",
    ],
    "include_msvcr": True,
    "optimize": 2,
}

shortcut_table = [
    (
        "DesktopShortcut",  # Shortcut
        "DesktopFolder",  # Directory_
        "Rare",  # Name
        "TARGETDIR",  # Component_
        "[TARGETDIR]Rare.exe",  # Target
        None,  # Arguments
        None,  # Description
        None,  # Hotkey
        None,  # Icon
        None,  # IconIndex
        None,  # ShowCmd
        "TARGETDIR",  # WkDir
    ),
]

msi_data = {
    "Shortcut": shortcut_table,
    "ProgId": [
        ("Prog.Id", None, None, _description, "IconId", None),
    ],
    "Icon": [("IcodId", f"{_icon}.ico")],
}

bdist_msi_options = {
    "data": msi_data,
    "license_file": _license,
    # generated with str(uuid.uuid3(uuid.NAMESPACE_DNS, 'io.github.dummerle.rare')).upper()
    "upgrade_code": "{85D9FCC2-733E-3D74-8DD4-8FE33A07ADF8}",
}

bdist_appimage_options = {
    "target_name": _name,
    "target_version": _version,
}

bdist_mac_options = {
    "iconfile": f"{_icon}.icns",
    "bundle_name": f"{_name}",
}

bdist_dmg_options = {
    "volume_label": _name,
    "applications_shortcut": True,
    "show_icon_preview": True,
    "license": {
        "default-language": "en_US",
        "licenses": {
            "en_US": _license,
        },
        "buttons": {
            "en_US": [
                "English", "Agree", "Disagree", "Print", "Save", "License"
            ]
        },
    },
}

executables = [
    Executable(
        script="rare/main.py",
        copyright=f"Copyright (C) 2024 {_author}",
        base="gui",
        icon=_icon,
        target_name=_name,
    ),
]

setup(
    name=_name,
    version=_version,
    author=_author,
    description=_description,
    executables=executables,
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
        "bdist_appimage": bdist_appimage_options,
        "bdist_mac": bdist_mac_options,
        "bdist_dmg": bdist_dmg_options,
    },
)
