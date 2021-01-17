# (Info Text, Type of input, legendary conf name, flags)
# possible flags: wine, path, only_int, binary(ComboBox), Combobox content([x,y,z])

default_settings = [
    ("Wine Prefix", "QLineEdit", "wine_prefix", ["wine", "path"]),
    ("Wine Executable", "QLineEdit", "wine_executable", ["wine"])
]

legendary_settings = [

    ("Locale", "QLineEdit", "locale"),
    ("Max Workers", "QLineEdit", "max_workers", ["only_int"]),
    ("Default install dir", "QLineEdit", "install_dir", ["path"]),
    ("Max Memory", "QLineEdit", "max_memory", ["only_int"]),
    ("EGL Sync", "QComboBox", "egl_sync", ["binary"]),
]

game_settings = default_settings + [
    ("Offline", "QComboBox", "offline", ["binary"]),
    ("Skip Update Check", "QComboBox", "skip_update_check", ["binary"]),
    ("Launch Parameter", "start_params", "QLineEdit"),
    ("Wrapper", "QLineEdit", "wrapper"),
    ("No Wine", "QComboBox", "no_wine", ["binary", "wine"])
]
