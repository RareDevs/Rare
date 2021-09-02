import sys

from cx_Freeze import setup, Executable

from rare import __version__

# Packages to include
python_packages = [
    "PyQt5",
    'requests',
    'PIL',
    'qtawesome',
    'psutil',
    'pypresence',
    'win32com'
]

# Modules to include
python_modules = []

base = None
name = None
build_options = {}
build_exe_options = {}
shortcutName = None
shortcutDir = None
bdist_msi_options = None
src_files = []
external_so_files = []

if sys.platform == 'win32':
    base = 'Win32GUI'
    name = 'Rare.exe'
    shortcut_table = [
        ('DesktopShortcut',  # Shortcut
         'DesktopFolder',  # Directory
         'Rare',  # Name
         'TARGETDIR',  # Component
         '[TARGETDIR]' + name,  # Target
         None,  # Arguments
         'A gui for Legendary.',  # Description
         None,  # Hotkey
         None,  # Icon
         None,  # IconIndex
         None,  # ShowCmd
         'TARGETDIR'  # Working Directory
         )]
    msi_data = {"Shortcut": shortcut_table}
    bdist_msi_options = {'data': msi_data, "all_users": False}
    build_options["bdist_msi"] = bdist_msi_options
else:
    name = 'Rare'

src_files += [
    'LICENSE',
    'README.md',
    'rare/resources/images/Rare.ico',
]

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options["packages"] = python_packages
build_exe_options["include_files"] = src_files + external_so_files
build_exe_options["includes"] = python_modules
build_exe_options["excludes"] = ["setuptools", "tkinter", "pkg_resources"]

# Set options
build_options["build_exe"] = build_exe_options

setup(name='Rare',
      version=__version__,
      description='A gui for Legendary.',
      options=build_options,
      executables=[
          Executable('rare/Rare.py',
                     target_name=name,
                     icon='rare/resources/images/Rare.ico',
                     base=base,
                     shortcut_name=shortcutName,
                     shortcut_dir=shortcutDir,
                     ),
      ],
      )
