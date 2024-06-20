from PySide6.QtWidgets import QGroupBox, QLayout

from rare.widgets.loading_widget import LoadingWidget


class StoreGroup(QGroupBox):
    def __init__(self, title: str, layout: type[QLayout], parent=None):
        super().__init__(parent=parent)
        self.setTitle(title)
        self.main_layout = layout(self)
        self.loading_widget = LoadingWidget(autostart=True, parent=self)

    def loading(self, state: bool) -> None:
        if state:
            self.loading_widget.start()
        else:
            self.loading_widget.stop()

