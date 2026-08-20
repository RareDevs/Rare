from logging import getLogger

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QPushButton

from rare.components.tabs.store.api.models.response import CatalogOfferModel
from rare.models.image import ImageSize
from rare.shared import RareCore
from rare.utils.misc import qta_icon
from rare.utils.qrequests import QRequests
from rare.widgets.image_widget import LoadingSpinnerImageWidget

from .icon_widget import IconWidget

logger = getLogger('StoreWidgets')


def is_offer_owned(rcore: RareCore | None, game: CatalogOfferModel) -> bool:
    if rcore is None or game is None:
        return False
    app_name = game.items[0].get('id') if game.items else game.id
    try:
        if rcore.core().is_installed(app_name):
            return True
    except Exception as e:  # noqa: BLE001
        logger.debug('Ownership check failed for %s: %s', app_name, e)
    entitlements = rcore.core().lgd.entitlements or []
    return any(
        ent.get('namespace') == game.namespace and ent.get('offerId') == game.id
        for ent in entitlements
    )


class ItemWidgetSpinner(LoadingSpinnerImageWidget):
    show_details = Signal(CatalogOfferModel)

    def __init__(self, manager: QRequests, catalog_game: CatalogOfferModel = None, rcore: RareCore | None = None, parent=None):
        super(ItemWidgetSpinner, self).__init__(manager, parent=parent)
        self.ui = IconWidget()
        self.catalog_game = catalog_game
        self.rcore = rcore

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.MouseButton.LeftButton:
            a0.accept()
            self.show_details.emit(self.catalog_game)
        if a0.button() == Qt.MouseButton.RightButton:
            a0.accept()


class StoreItemWidget(ItemWidgetSpinner):
    def __init__(self, manager: QRequests, catalog_game: CatalogOfferModel = None, rcore: RareCore | None = None, parent=None):
        super(StoreItemWidget, self).__init__(manager, catalog_game, rcore, parent=parent)
        self.setFixedSize(ImageSize.DisplayWide)
        self.ui.setupUi(self)
        if catalog_game:
            self.init_ui(catalog_game)

    def init_ui(self, game: CatalogOfferModel):
        if not game:
            self.ui.title_label.setText(self.tr('An error occurred'))
            return

        self.ui.title_label.setText(game.title)
        for attr in game.customAttributes:
            if attr['key'] == 'developerName':
                developer = attr['value']
                break
        else:
            developer = game.seller['name']
        self.ui.developer_label.setText(developer)

        if is_offer_owned(self.rcore, game):
            self.ui.price_label.setText(self.tr('Owned'))
            self.ui.discount_label.setVisible(False)
        else:
            price = game.price.totalPrice.fmtPrice['originalPrice']
            discount_price = game.price.totalPrice.fmtPrice['discountPrice']
            self.ui.price_label.setText(f'{price if price != "0" else self.tr("Free")}')
            if price != discount_price:
                font = self.ui.price_label.font()
                font.setStrikeOut(True)
                self.ui.price_label.setFont(font)
                self.ui.discount_label.setText(f'{discount_price if discount_price != "0" else self.tr("Free")}')
            else:
                self.ui.discount_label.setVisible(False)

        key_images = game.keyImages
        self.fetchPixmap(key_images.for_dimensions(self.width(), self.height()).url)


class SearchItemWidget(ItemWidgetSpinner):
    def __init__(self, manager: QRequests, catalog_game: CatalogOfferModel, rcore: RareCore | None = None, parent=None):
        super(SearchItemWidget, self).__init__(manager, catalog_game, rcore, parent=parent)
        self.setFixedSize(ImageSize.LibraryTall)
        self.ui.setupUi(self)

        key_images = catalog_game.keyImages
        self.fetchPixmap(key_images.for_dimensions(self.width(), self.height()).url)

        self.ui.title_label.setText(catalog_game.title)

        if is_offer_owned(self.rcore, catalog_game):
            self.ui.price_label.setText(self.tr('Owned'))
            self.ui.discount_label.setVisible(False)
        else:
            price = catalog_game.price.totalPrice.fmtPrice['originalPrice']
            discount_price = catalog_game.price.totalPrice.fmtPrice['discountPrice']
            self.ui.price_label.setText(f'{price if price != "0" else self.tr("Free")}')
            if price != discount_price:
                font = self.ui.price_label.font()
                font.setStrikeOut(True)
                self.ui.price_label.setFont(font)
                self.ui.discount_label.setText(f'{discount_price if discount_price != "0" else self.tr("Free")}')
            else:
                self.ui.discount_label.setVisible(False)


class WishlistItemWidget(ItemWidgetSpinner):
    delete_from_wishlist = Signal(CatalogOfferModel)

    def __init__(self, manager: QRequests, catalog_game: CatalogOfferModel, rcore: RareCore | None = None, parent=None):
        super(WishlistItemWidget, self).__init__(manager, catalog_game, rcore, parent=parent)
        self.setFixedSize(ImageSize.DisplayWide)
        self.ui.setupUi(self)

        for attr in catalog_game.customAttributes:
            if attr['key'] == 'developerName':
                developer = attr['value']
                break
        else:
            developer = catalog_game.seller['name']
        original_price = catalog_game.price.totalPrice.fmtPrice['originalPrice']
        discount_price = catalog_game.price.totalPrice.fmtPrice['discountPrice']

        self.ui.title_label.setText(catalog_game.title)
        self.ui.developer_label.setText(developer)
        if is_offer_owned(self.rcore, catalog_game):
            self.ui.price_label.setText(self.tr('Owned'))
            self.ui.discount_label.setVisible(False)
        else:
            self.ui.price_label.setText(f'{original_price if original_price != "0" else self.tr("Free")}')
            if original_price != discount_price:
                font = self.ui.price_label.font()
                font.setStrikeOut(True)
                self.ui.price_label.setFont(font)
                self.ui.discount_label.setText(f'{discount_price if discount_price != "0" else self.tr("Free")}')
            else:
                self.ui.discount_label.setVisible(False)
        key_images = catalog_game.keyImages
        self.fetchPixmap(key_images.for_dimensions(self.width(), self.height()).url)

        self.delete_button = QPushButton(self)
        self.delete_button.setIcon(qta_icon('mdi.delete', color='white'))
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.layout().insertWidget(0, self.delete_button, alignment=Qt.AlignmentFlag.AlignRight)

    @Slot()
    def _on_delete_clicked(self):
        self.delete_from_wishlist.emit(self.catalog_game)
