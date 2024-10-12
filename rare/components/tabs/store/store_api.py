from logging import getLogger
from typing import Callable, Tuple, Any

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QApplication

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
    update_wishlist = Signal()

    def __init__(self, token, language: str, country: str, installed):
        super(StoreAPI, self).__init__()
        self.token = token
        self.language_code: str = language
        self.country_code: str = country
        self.locale = f"{self.language_code}-{self.country_code}"
        self.manager = QtRequests(parent=self)
        self.authed_manager = QtRequests(token=token, parent=self)
        self.cached_manager = QtRequests(cache=str(cache_dir().joinpath("store")), parent=self)

        self.installed = installed

        self.browse_active = False
        self.next_browse_request = tuple(())

    def get_free(self, callback: callable):
        url = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions"
        params = {
            "locale": self.locale,
            "country": self.country_code,
            "allowCountries": self.country_code,
        }
        self.manager.get(url, lambda data: self.__handle_free_games(data, callback), params=params)

    @staticmethod
    def __handle_free_games(data, callback):
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    logger.error(error)
            elements = response.data.catalog.searchStore.elements
        except (Exception, AttributeError, KeyError) as e:
            if DEBUG():
                raise e
            elements = False
            logger.error("Free games request failed with: %s", e)
        callback(elements)

    def get_wishlist(self, callback):
        self.authed_manager.post(
            graphql_url,
            lambda data: self.__handle_wishlist(data, callback),
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
    def __handle_wishlist(data, callback):
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    logger.error(error)
            elements = response.data.wishlist.wishlistItems.elements
        except (Exception, AttributeError, KeyError) as e:
            if DEBUG():
                raise e
            elements = False
            logger.error("Wishlist request failed with: %s", e)
        callback(elements)

    def search_game(self, name, callback):
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

        self.manager.post(graphql_url, lambda data: self.__handle_search(data, callback), payload)

    @staticmethod
    def __handle_search(data, callback):
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    logger.error(error)
            elements = response.data.catalog.searchStore.elements
        except (Exception, AttributeError, KeyError) as e:
            if DEBUG():
                raise e
            elements = False
            logger.error("Search request failed with: %s", e)
        callback(elements)

    def browse_games(self, browse_model: SearchStoreQuery, callback):
        if self.browse_active:
            self.next_browse_request = (browse_model, callback)
            return
        self.browse_active = True
        payload = {
            "query": search_query,
            "variables": browse_model.to_dict()
        }
        self.manager.post(graphql_url, lambda data: self.__handle_browse_games(data, callback), payload)

    def __handle_browse_games(self, data, callback):
        self.browse_active = False
        if data is None:
            data = {}
        if not self.next_browse_request:
            try:
                response = ResponseModel.from_dict(data)
                if response.errors:
                    for error in response.errors:
                        logger.error(error)
                elements = response.data.catalog.searchStore.elements
            except (Exception, AttributeError, KeyError) as e:
                if DEBUG():
                    raise e
                elements = False
                logger.error("Browse request failed with: %s", e)
            callback(elements)
        else:
            self.browse_games(*self.next_browse_request)  # pylint: disable=E1120
            self.next_browse_request = tuple(())

    # def get_game_config_graphql(self, namespace: str, callback):
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

    def get_game_config_cms(self, slug: str, is_bundle: bool, callback):
        url = "https://store-content.ak.epicgames.com/api"
        url += f"/{self.locale}/content/{'products' if not is_bundle else 'bundles'}/{slug}"
        self.manager.get(url, lambda data: self.__handle_get_game(data, callback))

    @staticmethod
    def __handle_get_game(data, callback):
        try:
            product = DieselProduct.from_dict(data)
            callback(product)
        except Exception as e:
            if DEBUG():
                raise e
            logger.error(str(e))
            # callback({})

    # needs a captcha
    def add_to_wishlist(self, namespace, offer_id, callback: callable):
        payload = {
            "query": wishlist_add_query,
            "variables": {
                "offerId": offer_id,
                "namespace": namespace,
                "country": self.country_code,
                "locale": self.locale,
            },
        }
        self.authed_manager.post(graphql_url, lambda data: self._handle_add_to_wishlist(data, callback), payload)

    def _handle_add_to_wishlist(self, data, callback):
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    logger.error(error)
            success = response.data.wishlist.addToWishlist.success
        except Exception as e:
            if DEBUG():
                raise e
            logger.error("Add to wishlist request failed with: %s", e)
            success = False
        callback(success)
        self.update_wishlist.emit()

    def remove_from_wishlist(self, namespace, offer_id, callback: callable):
        payload = {
            "query": wishlist_remove_query,
            "variables": {
                "offerId": offer_id,
                "namespace": namespace,
                "operation": "REMOVE",
            },
        }
        self.authed_manager.post(graphql_url, lambda data: self._handle_remove_from_wishlist(data, callback),
                                 payload)

    def _handle_remove_from_wishlist(self, data, callback):
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    logger.error(error)
            success = response.data.wishlist.removeFromWishlist.success
        except Exception as e:
            if DEBUG():
                raise e
            logger.error("Remove from wishlist request failed with: %s", e)
            success = False
        callback(success)
        self.update_wishlist.emit()
