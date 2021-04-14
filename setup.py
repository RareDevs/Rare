import sys

from cx_Freeze import setup, Executable

import rare

opts = {
    'packages': [
        'requests',
        'PIL',
        'qtawesome',
        'notifypy',
        'psutil',
        'pypresence',
    ],
    'zip_include_packages': [
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
    ],
    'include_files': [
        'LICENSE',
        'README.MD',
        'rare/styles/Logo.ico',
    ],
}

setup_options = {'build_exe': opts}
base = None
name = None
shortcutName = None
shortcutDir = None
bdist_msi_options = None

if sys.platform == 'win32':
    base = 'Win32GUI'
    name = 'Rare.exe'
    shortcut_table = [
        ('DesktopShortcut',        # Shortcut
         'DesktopFolder',          # Directory
         'Rare',                   # Name
         'TARGETDIR',              # Component
         '[TARGETDIR]'+name,       # Target
         None,                     # Arguments
         'A gui for Legendary.',   # Description
         None,                     # Hotkey
         None,                     # Icon
         None,                     # IconIndex
         None,                     # ShowCmd
         'TARGETDIR'               # Working Directory
         )]
    msi_data = {"Shortcut": shortcut_table}
    bdist_msi_options = {'data': msi_data}
    setup_options.update({"bdist_msi": bdist_msi_options})
else:
    name = 'Rare'

setup(name = 'Rare',
    version = rare.__version__,
    description = 'A gui for Legendary.',
    options = setup_options,
    setup_requires=[
        'cx_Freeze',
    ],
    executables = [
        Executable('rare/__main__.py',
            targetName=name,
            icon='rare/styles/Logo.ico',
            base=base,
            shortcutName=shortcutName,
            shortcutDir=shortcutDir,
        ),
    ],
)
