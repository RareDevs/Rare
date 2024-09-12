import sys

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QDialog, QApplication, QVBoxLayout
from legendary.core import LegendaryCore

from . import StoreTab


class StoreWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.core = LegendaryCore()
        self.core.login()
        self.store_tab = StoreTab(self.core, self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.store_tab)

        self.store_tab.show()


if __name__ == "__main__":
    import rare.resources.static_css
    # import rare.resources.stylesheets.RareStyle
    from rare.utils.misc import set_style_sheet

    app = QApplication(sys.argv)
    app.setApplicationName("Rare")
    app.setOrganizationName("Rare")

    set_style_sheet("")
    set_style_sheet("RareStyle")
    window = StoreWindow()
    window.setWindowTitle(f"{app.applicationName()} - Store")
    window.resize(QSize(1280, 800))
    window.show()
    app.exec()
