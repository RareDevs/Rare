from dataclasses import dataclass, field
from email.message import Message
from logging import getLogger
from typing import Callable, Dict, List, Tuple, TypeVar, Union

import orjson
from PySide6.QtCore import QObject, QUrl, QUrlQuery, Signal, Slot
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkDiskCache,
    QNetworkReply,
    QNetworkRequest,
)

user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
# user_agent = f'UELauncher/{version} Windows/10.0.19041.1.256.64bit'
RequestHandler = TypeVar("RequestHandler", bound=Callable[[Union[Dict, bytes]], None])


@dataclass
class RequestQueueItem:
    method: str = None
    url: QUrl = None
    payload: Dict = field(default_factory=dict)
    params: Dict = field(default_factory=dict)
    handlers: List[RequestHandler] = field(default_factory=list)

    def __eq__(self, other):
        return self.method == other.method and self.url == other.url


class QtRequests(QObject):
    data_ready = Signal(object)

    def __init__(self, cache: str = None, token: str = None, parent=None):
        super(QtRequests, self).__init__(parent=parent)
        self.logger = getLogger(f"{type(self).__name__}_{type(parent).__name__}")
        self._manager = QNetworkAccessManager(self)
        self._manager.finished.connect(self.__on_finished)
        self._cache = None
        if cache is not None:
            self.logger.debug("Using cache dir %s", cache)
            self._cache = QNetworkDiskCache(self)
            self._cache.setCacheDirectory(cache)
            self._manager.setCache(self._cache)
        if token is not None:
            self.logger.debug("Manager is authorized")
        self._token = token

        self.__active_requests: Dict[QNetworkReply, RequestQueueItem] = {}

    @staticmethod
    def __prepare_query(url, params) -> QUrl:
        url = QUrl(url)
        query = QUrlQuery(url)
        for k, v in params.items():
            query.addQueryItem(str(k), str(v))
        url.setQuery(query)
        return url

    def __prepare_request(self, item: RequestQueueItem) -> QNetworkRequest:
        request = QNetworkRequest(item.url)
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader,
            "application/json; charset=UTF-8",
        )
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, user_agent)
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        if self._cache is not None:
            request.setAttribute(
                QNetworkRequest.Attribute.CacheLoadControlAttribute,
                QNetworkRequest.CacheLoadControl.PreferCache,
            )
        if self._token is not None:
            request.setRawHeader(b"Authorization", self._token.encode())
        return request

    def __post(self, item: RequestQueueItem):
        request = self.__prepare_request(item)
        payload = orjson.dumps(item.payload)
        reply = self._manager.post(request, payload)
        reply.errorOccurred.connect(self.__on_error)
        self.__active_requests[reply] = item

    def post(self, url: str, handler: RequestHandler, payload: dict):
        item = RequestQueueItem(method="post", url=QUrl(url), payload=payload, handlers=[handler])
        self.__post(item)

    def __get(self, item: RequestQueueItem):
        request = self.__prepare_request(item)
        reply = self._manager.get(request)
        reply.errorOccurred.connect(self.__on_error)
        self.__active_requests[reply] = item

    def get(
        self,
        url: str,
        handler: RequestHandler,
        payload: Dict = None,
        params: Dict = None,
    ):
        url = self.__prepare_query(url, params) if params is not None else QUrl(url)
        item = RequestQueueItem(method="get", url=url, payload=payload, handlers=[handler])
        self.__get(item)

    def __on_error(self, error: QNetworkReply.NetworkError) -> None:
        self.logger.error(error)

    @staticmethod
    def __parse_content_type(header) -> Tuple[str, str]:
        # lk: this looks weird but `cgi` is deprecated, PEP 594 suggests this way of parsing MIME
        m = Message()
        m["content-type"] = header
        return m.get_content_type(), m.get_content_charset()

    @Slot(QNetworkReply)
    def __on_finished(self, reply: QNetworkReply):
        item = self.__active_requests.pop(reply, None)
        if item is None:
            self.logger.error("QNetworkReply: %s without associated item", reply.url().toString())
        elif reply.error() != QNetworkReply.NetworkError.NoError:
            self.logger.error(reply.errorString())
        else:
            mimetype, charset = self.__parse_content_type(reply.header(QNetworkRequest.KnownHeaders.ContentTypeHeader))
            maintype, subtype = mimetype.split("/")
            bin_data = reply.readAll().data()
            if mimetype == "application/json":
                data = orjson.loads(bin_data)
            elif maintype == "image":
                data = bin_data
            else:
                data = None
            for handler in item.handlers:
                handler(data)
        reply.disconnect(reply)
        reply.deleteLater()
