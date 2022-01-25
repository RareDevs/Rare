from cx_Freeze import setup, Executable

from rare import __version__

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
    )
]

msi_data = {"Shortcut": shortcut_table}
bdist_msi_options = {"data": msi_data}
base = "Win32GUI"

setup(
    name="Rare",
    version=__version__,
    description="A GUI for Legendary",
    options={
        "bdist_msi": bdist_msi_options,
    },
    executables=[
        Executable(
            "rare/__main__.py",
            base=base,
            icon="rare/resources/images/Rare.ico",
            target_name="Rare",
        )
    ],
)
