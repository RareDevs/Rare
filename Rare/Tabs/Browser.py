from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage


class BrowserTab(QWebEngineView):
    def __init__(self):
        super(BrowserTab, self).__init__()
        self.profile = QWebEngineProfile("storage", self)
        self.webpage = QWebEnginePage(self.profile, self)
        self.webpage.javaScriptConsoleMessage = lambda level, msg, line, sourceID: None
        self.setPage(self.webpage)
        self.load(QUrl("https://www.epicgames.com/store/"))
        self.show()

    def createWindow(self, QWebEnginePage_WebWindowType):
        return self
