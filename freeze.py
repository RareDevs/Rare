from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only

requirements = [
    "requests",
    "PIL",
    "setuptools",
    "wheel",
    "PyQt5",
    "qtawesome",
    "notifypy",
    "psutil",
    "pypresence",
    'win32com'
]

bdist_msi_options = {
    'add_to_path': False,
    'initial_target_dir': r'[ProgramFilesFolder]\%s' % "Rare",
}
build_exe_options = {"includes": requirements, "excludes": ["tkinter", "setuptools"]}

base = "Win32GUI"

setup(
    name="Rare",
    version="1.5.0",
    description="A GUI for Legendary",
    options={"build_exe": build_exe_options},
    shortcutName="Rare",
    shortcutDir="DesktopFolder",
    executables=[Executable("rare/__main__.py",
                            base=base, icon="rare/resources/images/Rare.ico")]
)
