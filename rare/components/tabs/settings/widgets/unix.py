from components.tabs.settings import LinuxSettings


class LinuxAppSettings(LinuxSettings):
    def __init__(self, parent=None):
        super(LinuxAppSettings, self).__init__(parent=parent)

    def update_game(self, app_name):
        self.name = app_name
        self.wine_prefix.setText(self.load_prefix())
        self.wine_exec.setText(self.load_setting(self.name, "wine_executable"))

        self.dxvk.load_settings(self.name)

        self.mangohud.load_settings(self.name)