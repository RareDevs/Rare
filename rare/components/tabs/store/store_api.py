from collections.abc import Callable
from logging import getLogger

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from rare.components.tabs.store.constants import (
    purchase_query,
    search_query,
    wishlist_add_query,
    wishlist_query,
    wishlist_remove_query,
)
from rare.utils.qrequests import QRequests

from .api.models.diesel import DieselProduct
from .api.models.query import SearchStoreQuery
from .api.models.response import (
    ResponseModel,
)

graphql_url = 'https://launcher.store.epicgames.com/graphql'


def DEBUG() -> bool:
    return '--debug' in QApplication.arguments()


class StoreAPI(QObject):
    update_wishlist = Signal()

    def __init__(self, token, language: str, country: str, installed, user_agent: str):
        super(StoreAPI, self).__init__()
        self.logger = getLogger(type(self).__name__)
        self.token = token
        self.language_code: str = language
        self.country_code: str = country
        self.locale = f'{self.language_code}-{self.country_code}'
        self.manager = QRequests(parent=self)
        self.authed_manager = QRequests(token=token, user_agent=user_agent, parent=self)
        self.image_manager = QRequests(parent=self)

        self.installed = installed

        self.browse_active = False
        self.next_browse_request = ()

    def get_free(self, callback: Callable):
        url = 'https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions'
        params = {
            'locale': self.locale,
            'country': self.country_code,
            'allowCountries': self.country_code,
        }
        self.manager.get(url, lambda data: self.__handle_free_games(data, callback), params=params)

    def __handle_free_games(self, data, callback: Callable):
        elements = False
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    self.logger.error('Free games request failed: %s', error)
                callback(elements)
                return
            if (
                response.data is None
                or response.data.catalog is None
                or response.data.catalog.searchStore is None
            ):
                self.logger.error('Free games request returned no data')
                callback(elements)
                return
            elements = response.data.catalog.searchStore.elements
        except (Exception, AttributeError, KeyError) as e:
            if DEBUG():
                raise
            self.logger.error('Free games request failed with: %s', e)
        callback(elements)

    def get_wishlist(self, callback: Callable):
        self.authed_manager.post(
            graphql_url,
            lambda data: self.__handle_wishlist(data, callback),
            {
                'query': wishlist_query,
                'variables': {
                    'country': self.country_code,
                    'locale': self.locale,
                    'withPrice': True,
                },
            },
        )

    def __handle_wishlist(self, data, callback: Callable[[tuple], None]):
        elements = False
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    self.logger.error('Wishlist request failed: %s', error)
                callback(elements)
                return
            if (
                response.data is None
                or response.data.wishlist is None
                or response.data.wishlist.wishlistItems is None
            ):
                self.logger.error('Wishlist request returned no data')
                callback(elements)
                return
            elements = response.data.wishlist.wishlistItems.elements
        except (Exception, AttributeError, KeyError) as e:
            if DEBUG():
                raise
            self.logger.error('Wishlist request failed with: %s', e)
        callback(elements)

    def search_game(self, name, callback: Callable):
        payload = {
            'query': search_query,
            'variables': {
                'category': 'games/edition/base|bundles/games|editors|software/edition/base',
                'count': 20,
                'country': self.country_code,
                'keywords': name,
                'locale': self.locale,
                'sortDir': 'DESC',
                'allowCountries': self.country_code,
                'start': 0,
                'tag': '',
                'withMapping': False,
                'withPrice': True,
            },
        }

        self.authed_manager.post(graphql_url, lambda data: self.__handle_search(data, callback), payload)

    def __handle_search(self, data, callback: Callable[[tuple], None]):
        elements = False
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    self.logger.error('Search request failed: %s', error)
                callback(elements)
                return
            if (
                response.data is None
                or response.data.catalog is None
                or response.data.catalog.searchStore is None
            ):
                self.logger.error('Search request returned no data')
                callback(elements)
                return
            elements = response.data.catalog.searchStore.elements
        except (Exception, AttributeError, KeyError) as e:
            if DEBUG():
                raise
            self.logger.error('Search request failed with: %s', e)
        callback(elements)

    def browse_games(self, browse_model: SearchStoreQuery, callback):
        if self.browse_active:
            self.next_browse_request = (browse_model, callback)
            return
        self.browse_active = True
        payload = {'query': search_query, 'variables': browse_model.to_dict()}
        self.authed_manager.post(
            graphql_url,
            lambda data: self.__handle_browse_games(data, callback),
            payload,
        )

    def __handle_browse_games(self, data, callback):
        self.browse_active = False
        if self.next_browse_request:
            self.browse_games(*self.next_browse_request)  # pylint: disable=E1120
            self.next_browse_request = ()
            return
        if data is None:
            self.logger.error('Browse request failed')
            callback(False)
            return
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    self.logger.error('Browse request failed: %s', error)
                callback(False)
                return
            if (
                response.data is None
                or response.data.catalog is None
                or response.data.catalog.searchStore is None
            ):
                self.logger.error('Browse request returned no data')
                callback(False)
                return
            elements = response.data.catalog.searchStore.elements
        except (Exception, AttributeError, KeyError) as e:
            if DEBUG():
                raise
            elements = False
            self.logger.error('Browse request failed with: %s', e)
        callback(elements)

    def get_game_config_cms(self, slug: str, is_bundle: bool, callback: Callable):
        url = 'https://store-content.ak.epicgames.com/api'
        url += f'/{self.locale}/content/{"products" if not is_bundle else "bundles"}/{slug}'
        self.logger.debug('Quering game config: %s', url)
        self.manager.get(url, lambda data: self.__handle_get_game(data, callback))

    def __handle_get_game(self, data, callback):
        try:
            product = DieselProduct.from_dict(data)
            callback(product)
        except Exception as e:
            if DEBUG():
                raise
            self.logger.error(str(e))
            # callback({})

    # needs a captcha
    def add_to_wishlist(self, namespace, offer_id, callback: Callable):
        payload = {
            'query': wishlist_add_query,
            'variables': {
                'offerId': offer_id,
                'namespace': namespace,
                'country': self.country_code,
                'locale': self.locale,
            },
        }
        self.authed_manager.post(
            graphql_url,
            lambda data: self._handle_add_to_wishlist(data, callback),
            payload,
        )

    def _handle_add_to_wishlist(self, data, callback):
        success = False
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    self.logger.error('Add to wishlist request failed: %s', error)
                callback(success)
                return
            if (
                response.data is None
                or response.data.wishlist is None
                or response.data.wishlist.addToWishlist is None
            ):
                self.logger.error('Add to wishlist request returned no data')
                callback(success)
                return
            success = response.data.wishlist.addToWishlist.success
        except Exception as e:
            if DEBUG():
                raise
            self.logger.error('Add to wishlist request failed with: %s', e)
        callback(success)
        self.update_wishlist.emit()

    def remove_from_wishlist(self, namespace, offer_id, callback: Callable):
        payload = {
            'query': wishlist_remove_query,
            'variables': {
                'offerId': offer_id,
                'namespace': namespace,
                'operation': 'REMOVE',
            },
        }
        self.authed_manager.post(
            graphql_url,
            lambda data: self._handle_remove_from_wishlist(data, callback),
            payload,
        )

    def _handle_remove_from_wishlist(self, data, callback):
        success = False
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    self.logger.error('Remove from wishlist request failed: %s', error)
                callback(success)
                return
            if (
                response.data is None
                or response.data.wishlist is None
                or response.data.wishlist.removeFromWishlist is None
            ):
                self.logger.error('Remove from wishlist request returned no data')
                callback(success)
                return
            success = response.data.wishlist.removeFromWishlist.success
        except Exception as e:
            if DEBUG():
                raise
            self.logger.error('Remove from wishlist request failed with: %s', e)
        callback(success)
        self.update_wishlist.emit()

    def purchase_free_game(self, namespace: str, offer_id: str, callback: Callable[[bool], None]):
        payload = {
            'query': purchase_query,
            'variables': {
                'namespace': namespace,
                'offerId': offer_id,
                'country': self.country_code,
                'locale': self.locale,
            },
        }
        self.authed_manager.post(
            graphql_url,
            lambda data: self._handle_purchase(data, callback),
            payload,
        )

    def _handle_purchase(self, data, callback: Callable[[bool], None]):
        success = False
        try:
            response = ResponseModel.from_dict(data)
            if response.errors:
                for error in response.errors:
                    self.logger.error('Purchase request failed: %s', error)
                callback(success)
                return
            if (
                response.data is None
                or response.data.catalog is None
                or response.data.catalog.purchase is None
            ):
                self.logger.error('Purchase request returned no data')
                callback(success)
                return
            code = response.data.catalog.purchase.code
            success = code in {'OK', 'ALREADY_IN_LIBRARY', 'OK_NO_CHANGE'}
        except Exception as e:
            if DEBUG():
                raise
            self.logger.error('Purchase request failed with: %s', e)
            success = False
        callback(success)
