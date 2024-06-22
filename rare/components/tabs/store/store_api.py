from logging import getLogger
from typing import Callable, Tuple

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication

from rare.components.tabs.store.constants import (
    wishlist_query,
    search_query,
    wishlist_add_query,
    wishlist_remove_query,
)
from rare.utils.paths import cache_dir
from rare.utils.qt_requests import QtRequests
from .api.models.query import SearchStoreQuery
from .api.models.diesel import DieselProduct
from .api.models.response import (
    ResponseModel,
    CatalogOfferModel,
)

logger = getLogger("StoreAPI")
graphql_url = "https://graphql.epicgames.com/graphql"


DEBUG: Callable[[], bool] = lambda: "--debug" in QApplication.arguments()


class StoreAPI(QObject):
    update_wishlist = pyqtSignal()

    def __init__(self, token, language: str, country: str, installed):
        super(StoreAPI, self).__init__()
        self.token = token
        self.language_code: str = language
        self.country_code: str = country
        self.locale = f"{self.language_code}-{self.country_code}"
        self.locale = "en-US"
        self.manager = QtRequests(parent=self)
        self.authed_manager = QtRequests(token=token, parent=self)
        self.cached_manager = QtRequests(cache=str(cache_dir().joinpath("store")), parent=self)

        self.installed = installed

        self.browse_active = False
        self.next_browse_request = tuple(())

    def get_free(self, handle_func: callable):
        url = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions"
        params = {
            "locale": self.locale,
            "country": self.country_code,
            "allowCountries": self.country_code,
        }
        self.manager.get(url, lambda data: self.__handle_free_games(data, handle_func), params=params)

    @staticmethod
    def __handle_free_games(data, handle_func):
        try:
            response = ResponseModel.from_dict(data)
            results: Tuple[CatalogOfferModel, ...] = response.data.catalog.searchStore.elements
            handle_func(results)
        except KeyError as e:
            if DEBUG():
                raise e
            logger.error("Free games Api request failed")
            handle_func(["error", "Key error"])
            return
        except Exception as e:
            if DEBUG():
                raise e
            logger.error(f"Free games Api request failed: {e}")
            handle_func(["error", e])
            return

    def get_wishlist(self, handle_func):
        self.authed_manager.post(
            graphql_url,
            lambda data: self.__handle_wishlist(data, handle_func),
            {
                "query": wishlist_query,
                "variables": {
                    "country": self.country_code,
                    "locale": self.locale,
                    "withPrice": True,
                },
            },
        )

    @staticmethod
    def __handle_wishlist(data, handle_func):
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                logger.error(response.errors)
            handle_func(response.data.wishlist.wishlistItems.elements)
        except KeyError as e:
            if DEBUG():
                raise e
            logger.error("Free games API request failed")
            handle_func(["error", "Key error"])
            return
        except Exception as e:
            if DEBUG():
                raise e
            logger.error(f"Free games API request failed")
            handle_func(["error", e])
            return

    def search_game(self, name, handler):
        payload = {
            "query": search_query,
            "variables": {
                "category": "games/edition/base|bundles/games|editors|software/edition/base",
                "count": 20,
                "country": self.country_code,
                "keywords": name,
                "locale": self.locale,
                "sortDir": "DESC",
                "allowCountries": self.country_code,
                "start": 0,
                "tag": "",
                "withMapping": False,
                "withPrice": True,
            },
        }

        self.manager.post(graphql_url, lambda data: self.__handle_search(data, handler), payload)

    @staticmethod
    def __handle_search(data, handler):
        try:
            response = ResponseModel.from_dict(data)
            handler(response.data.catalog.searchStore.elements)
        except KeyError as e:
            if DEBUG():
                raise e
            logger.error(str(e))
            handler([])
        except Exception as e:
            if DEBUG():
                raise e
            logger.error(f"Search Api request failed: {e}")
            handler([])
            return

    def browse_games(self, browse_model: SearchStoreQuery, handle_func):
        if self.browse_active:
            self.next_browse_request = (browse_model, handle_func)
            return
        self.browse_active = True
        payload = {
            "query": search_query,
            "variables": browse_model.to_dict()
        }
        self.manager.post(graphql_url, lambda data: self.__handle_browse_games(data, handle_func), payload)

    def __handle_browse_games(self, data, handle_func):
        self.browse_active = False
        if data is None:
            data = {}
        if not self.next_browse_request:
            try:
                response = ResponseModel.from_dict(data)
                handle_func(response.data.catalog.searchStore.elements)
            except KeyError as e:
                if DEBUG():
                    raise e
                logger.error(str(e))
                handle_func([])
            except Exception as e:
                if DEBUG():
                    raise e
                logger.error(f"Browse games Api request failed: {e}")
                handle_func([])
                return
        else:
            self.browse_games(*self.next_browse_request)  # pylint: disable=E1120
            self.next_browse_request = tuple(())

    # def get_game_config_graphql(self, namespace: str, handle_func):
    #     payload = {
    #         "query": config_query,
    #         "variables": {
    #             "namespace": namespace
    #         }
    #     }

    def __make_graphql_query(self):
        pass

    def __make_api_query(self):
        pass

    def get_game_config_cms(self, slug: str, is_bundle: bool, handle_func):
        url = "https://store-content.ak.epicgames.com/api"
        url += f"/{self.locale}/content/{'products' if not is_bundle else 'bundles'}/{slug}"
        self.manager.get(url, lambda data: self.__handle_get_game(data, handle_func))

    @staticmethod
    def __handle_get_game(data, handle_func):
        try:
            product = DieselProduct.from_dict(data)
            handle_func(product)
        except Exception as e:
            if DEBUG():
                raise e
            logger.error(str(e))
            # handle_func({})

    # needs a captcha
    def add_to_wishlist(self, namespace, offer_id, handle_func: callable):
        payload = {
            "query": wishlist_add_query,
            "variables": {
                "offerId": offer_id,
                "namespace": namespace,
                "country": self.country_code,
                "locale": self.locale,
            },
        }
        self.authed_manager.post(graphql_url, lambda data: self._handle_add_to_wishlist(data, handle_func), payload)

    def _handle_add_to_wishlist(self, data, handle_func):
        try:
            response = ResponseModel.from_dict(data)
            data = response.data.wishlist.addToWishlist
            handle_func(data.success)
        except Exception as e:
            if DEBUG():
                raise e
            logger.error(str(e))
            handle_func(False)
        self.update_wishlist.emit()

    def remove_from_wishlist(self, namespace, offer_id, handle_func: callable):
        payload = {
            "query": wishlist_remove_query,
            "variables": {
                "offerId": offer_id,
                "namespace": namespace,
                "operation": "REMOVE",
            },
        }
        self.authed_manager.post(graphql_url, lambda data: self._handle_remove_from_wishlist(data, handle_func),
                                 payload)

    def _handle_remove_from_wishlist(self, data, handle_func):
        try:
            response = ResponseModel.from_dict(data)
            data = response.data.wishlist.removeFromWishlist
            handle_func(data.success)
        except Exception as e:
            if DEBUG():
                raise e
            logger.error(str(e))
            handle_func(False)
        self.update_wishlist.emit()
