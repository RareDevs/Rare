import json
from dataclasses import dataclass
from logging import getLogger
from typing import Callable
from typing import Union

from PyQt5.QtCore import QObject, pyqtSignal, QUrl, QJsonParseError, QJsonDocument
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

logger = getLogger("QtRequests")


class QtRequestManager(QObject):
    data_ready = pyqtSignal(object)
    request = None
    request_active = None

    def __init__(self, type: str = "json", authorization_token: str = None):
        super(QtRequestManager, self).__init__()
        self.manager = QNetworkAccessManager()
        self.type = type
        self.authorization_token = authorization_token
        self.request_queue = []

    def post(self, url: str, payload: dict, handle_func):
        if not self.request_active:
            request = QNetworkRequest(QUrl(url))
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            self.request_active = RequestQueueItem(handle_func=handle_func)
            payload = json.dumps(payload).encode("utf-8")

            request.setHeader(QNetworkRequest.UserAgentHeader,
                              "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36")

            if self.authorization_token is not None:
                request.setRawHeader(b"Authorization", self.authorization_token.encode())

            self.request = self.manager.post(request, payload)
            self.request.finished.connect(self.prepare_data)

        else:
            self.request_queue.append(
                RequestQueueItem(method="post", url=url, payload=payload, handle_func=handle_func))

    def get(self, url: str, handle_func: Callable[[Union[dict, bytes]], None]):
        if not self.request_active:
            request = QNetworkRequest(QUrl(url))
            request.setHeader(QNetworkRequest.UserAgentHeader,
                              "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36")

            self.request_active = RequestQueueItem(handle_func=handle_func)
            self.request = self.manager.get(request)
            self.request.finished.connect(self.prepare_data)
        else:
            self.request_queue.append(RequestQueueItem(method="get", url=url, handle_func=handle_func))

    def prepare_data(self):
        # self.request_active = False
        data = {} if self.type == "json" else b""
        if self.request:
            try:
                if self.request.error() == QNetworkReply.NoError:
                    if self.type == "json":
                        error = QJsonParseError()
                        json_data = QJsonDocument.fromJson(self.request.readAll().data(), error)
                        if QJsonParseError.NoError == error.error:
                            data = json.loads(json_data.toJson().data().decode())
                        else:
                            logger.error(error.errorString())
                    else:
                        data = self.request.readAll().data()

            except RuntimeError as e:
                logger.error(str(e))
        self.request_active.handle_func(data)
        self.request.deleteLater()
        self.request_active = None

        if self.request_queue:
            if self.request_queue[0].method == "post":
                self.post(self.request_queue[0].url, self.request_queue[0].payload, self.request_queue[0].handle_func)
            else:
                self.get(self.request_queue[0].url, self.request_queue[0].handle_func)
            self.request_queue.pop(0)


@dataclass
class RequestQueueItem:
    method: str = None
    url: str = None
    handle_func: Callable[[Union[dict, bytes]], None] = None
    payload: dict = None
