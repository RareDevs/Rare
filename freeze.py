from cx_Freeze import setup, Executable

from rare import __version__

name = 'Rare'
author = 'Dummerle'
description = 'A GUI for Legendary'

shortcut_table = [
    ("DesktopShortcut",  # Shortcut
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
     'TARGETDIR'  # WkDir
     )
]

msi_data = {"Shortcut": shortcut_table}
bdist_msi_options = {
    'data': msi_data,
    # generated with str(uuid.uuid3(uuid.NAMESPACE_DNS, 'io.github.dummerle.rare')).upper()
    'upgrade_code': '{85D9FCC2-733E-3D74-8DD4-8FE33A07ADF8}'
}
base = "Win32GUI"

exe = Executable(
    "rare/main.py",
    base=base,
    icon="rare/resources/images/Rare.ico",
    target_name=name
)

setup(
    name=name,
    version=__version__,
    author=author,
    description=description,
    options={
        "bdist_msi": bdist_msi_options,
    },
    executables=[exe]
)
