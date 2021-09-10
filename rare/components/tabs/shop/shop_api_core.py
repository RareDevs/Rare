from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QObject

from rare.components.tabs.shop.constants import wishlist_query, search_query, game_query, add_to_wishlist_query, \
    remove_from_wishlist_query
from rare.components.tabs.shop.shop_models import BrowseModel
from rare.utils.qt_requests import QtRequestManager
from rare.utils.utils import get_lang

logger = getLogger("ShopAPICore")
graphql_url = "https://www.epicgames.com/graphql"


class ShopApiCore(QObject):
    update_wishlist = pyqtSignal()

    def __init__(self, auth_token):
        super(ShopApiCore, self).__init__()
        self.token = auth_token
        self.manager = QtRequestManager()
        self.auth_manager = QtRequestManager(authorization_token=auth_token)
        self.locale = get_lang()

        self.browse_active = False
        self.next_browse_request = tuple(())

    def get_free_games(self, handle_func: callable):
        url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"

        self.manager.get(url, lambda data: self._handle_free_games(data, handle_func))

    def _handle_free_games(self, data, handle_func):
        try:
            handle_func(data["data"]["Catalog"]["searchStore"]["elements"])
        except KeyError as e:
            logger.error(str(e))

    def get_wishlist(self, handle_func):
        self.auth_manager.post(graphql_url, {
            "query": wishlist_query,
            "variables": {
                "country": self.locale.upper(),
                "locale": self.locale
            }
        }, lambda data: self._handle_wishlist(data, handle_func))

    def _handle_wishlist(self, data, handle_func):
        handle_func(data["data"]["Wishlist"]["wishlistItems"]["elements"])

    def search_game(self, name, handle_func):
        payload = {
            "query": search_query,
            "variables": {"category": "games/edition/base|bundles/games|editors|software/edition/base", "count": 1,
                          "country": "DE", "keywords": name, "locale": self.locale, "sortDir": "DESC",
                          "allowCountries": self.locale.upper(),
                          "start": 0, "tag": "", "withMapping": False, "withPrice": True}
        }

        self.manager.post(graphql_url, payload, lambda data: self._handle_search(data, handle_func))

    def _handle_search(self, data, handle_func):
        handle_func(data["data"]["Catalog"]["searchStore"]["elements"])

    def browse_games(self, browse_model: BrowseModel, handle_func):
        if self.browse_active:
            self.next_browse_request = (browse_model, handle_func)
            return
        self.browse_active = True
        payload = {
            "variables": browse_model.__dict__,
            "query": game_query
        }

        self.auth_manager.post(graphql_url, payload, lambda data: self._handle_browse_games(data, handle_func))

    def _handle_browse_games(self, data, handle_func):
        self.browse_active = False
        if not self.next_browse_request:
            handle_func(data["data"]["Catalog"]["searchStore"]["elements"])
        else:
            self.browse_games(*self.next_browse_request)
            self.next_browse_request = tuple(())

    def get_game(self, slug: str, is_bundle: bool, handle_func):
        url = f"https://store-content.ak.epicgames.com/api/{self.locale}/content/{'products' if not is_bundle else 'bundles'}/{slug}"
        self.manager.get(url, lambda data: self._handle_get_game(data, handle_func))

    def _handle_get_game(self, data, handle_func):
        handle_func(data)

    def add_to_wishlist(self, namespace, offer_id, handle_func: callable):
        payload = {
            "variables": {
                "offerId": offer_id,
                "namespace": namespace,
                "country": self.locale.upper(),
                "locale": self.locale
            },
            "query": add_to_wishlist_query
        }
        self.auth_manager.post(graphql_url, payload, lambda data: self._handle_add_to_wishlist(data, handle_func))

    def _handle_add_to_wishlist(self, data, handle_func):
        try:
            data = data["data"]["Wishlist"]["addToWishlist"]
            if data["success"]:
                handle_func(True)
            else:
                handle_func(False)
        except Exception as e:
            logger.error(str(e))
            handle_func(False)
        self.update_wishlist.emit()

    def remove_from_wishlist(self, namespace, offer_id, handle_func: callable):
        payload = {
            "variables": {
                "offerId": offer_id,
                "namespace": namespace,
                "operation": "REMOVE"
            },
            "query": remove_from_wishlist_query
        }
        self.auth_manager.post(graphql_url, payload, lambda data: self._handle_remove_from_wishlist(data, handle_func))

    def _handle_remove_from_wishlist(self, data, handle_func):
        try:
            data = data["data"]["Wishlist"]["removeFromWishlist"]
            if data["success"]:
                handle_func(True)
            else:
                handle_func(False)
        except Exception as e:
            logger.error(str(e))
            handle_func(False)
        self.update_wishlist.emit()