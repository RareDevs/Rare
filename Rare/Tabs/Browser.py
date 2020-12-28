from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage


class BrowserTab(QWebEngineView):
    def __init__(self, parent):
        super(BrowserTab, self).__init__(parent=parent)
        self.profile = QWebEngineProfile("storage", self)
        self.webpage = QWebEnginePage(self.profile, self)
        self.setPage(self.webpage)
        self.load(QUrl("https://www.epicgames.com/store/"))
        self.show()

    def createWindow(self, QWebEnginePage_WebWindowType):
        return self
