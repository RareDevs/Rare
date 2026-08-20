from logging import getLogger

from PySide6.QtCore import Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QKeyEvent
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from rare.components.tabs.store.api.models.diesel import (
    DieselProduct,
    DieselProductDetail,
    DieselSystemDetail,
)
from rare.components.tabs.store.api.models.response import CatalogOfferModel
from rare.components.tabs.store.store_api import StoreAPI
from rare.models.image import ImageSize
from rare.models.install import InstallOptionsModel
from rare.shared import RareCore
from rare.ui.components.tabs.store.details import Ui_StoreDetailsWidget
from rare.utils.misc import qta_icon
from rare.widgets.elide_label import ElideLabel
from rare.widgets.image_widget import LoadingSpinnerImageWidget
from rare.widgets.side_tab import SideTabBar, SideTabContents, SideTabWidget

logger = getLogger('StoreDetails')


class StoreDetailsWidget(QWidget, SideTabContents):
    back_clicked: Signal = Signal()
    open_library: Signal = Signal()

    # TODO Design
    def __init__(self, rcore: RareCore | None, store_api: StoreAPI, parent=None):
        super(StoreDetailsWidget, self).__init__(parent=parent)
        self.implements_scrollarea = True

        self.ui = Ui_StoreDetailsWidget()
        self.ui.setupUi(self)
        self.ui.main_layout.setContentsMargins(0, 0, 3, 0)

        self.rcore = rcore
        self.store_api = store_api
        self.catalog_offer: CatalogOfferModel = None
        self._primary_mode: str | None = None

        self.image = LoadingSpinnerImageWidget(store_api.image_manager, self)
        self.image.setFixedSize(ImageSize.DisplayTall)
        self.ui.left_layout.insertWidget(0, self.image, alignment=Qt.AlignmentFlag.AlignTop)
        self.ui.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.ui.wishlist_button.clicked.connect(self.add_to_wishlist)
        self.ui.store_button.clicked.connect(self.on_primary_action)
        self.ui.wishlist_button.setVisible(True)
        self.in_wishlist = False
        self.wishlist = []

        self.requirements_tabs = SideTabWidget(
            tab_orientation=SideTabBar.TabOrientation.Vertical, parent=self.ui.requirements_frame
        )
        self.requirements_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ui.requirements_layout.setContentsMargins(0, 0, 0, 0)
        self.ui.requirements_layout.addWidget(self.requirements_tabs)
        self.ui.requirements_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.ui.back_button.setIcon(qta_icon('fa.chevron-left', 'fa5s.chevron-left'))
        self.ui.back_button.clicked.connect(self.back_clicked)

        self.setDisabled(False)

    def handle_wishlist_update(self, wishlist: list[CatalogOfferModel]):
        if wishlist and wishlist[0] == 'error':
            return
        self.wishlist = [game.id for game in wishlist]
        if self.id_str in self.wishlist:
            self.in_wishlist = True
            self.ui.wishlist_button.setText(self.tr('Remove from Wishlist'))
        else:
            self.in_wishlist = False

    def update_game(self, offer: CatalogOfferModel):
        self.ui.title.setText(offer.title)
        self.title_str = offer.title
        self.id_str = offer.id
        self.store_api.get_wishlist(self.handle_wishlist_update)

        # lk: delete tabs in reverse order because indices are updated on deletion
        while self.requirements_tabs.count():
            self.requirements_tabs.widget(0).disconnect(self.requirements_tabs.widget(0))
            self.requirements_tabs.widget(0).deleteLater()
            self.requirements_tabs.removeTab(0)
        self.requirements_tabs.clear()

        slug = offer.productSlug
        if not slug:
            for mapping in offer.offerMappings:
                if mapping['pageType'] == 'productHome':
                    slug = mapping['pageSlug']
                    break
            else:
                logger.error('Could not get page information')
                slug = ''
        if '/home' in slug:
            slug = slug.replace('/home', '')
        self.slug = slug

        self._update_primary_action(offer)

        self.ui.original_price.setText(self.tr('Loading'))
        # self.title.setText(self.tr("Loading"))
        # self.image.setPixmap(QPixmap())
        is_bundle = False
        for i in offer.categories:
            if 'bundles' in i.get('path', ''):
                is_bundle = True

        # init API request
        if slug:
            self.store_api.get_game_config_cms(offer.productSlug, is_bundle, self.data_received)
        # else:
        #     self.data_received({})
        self.catalog_offer = offer

    def add_to_wishlist(self):
        if not self.in_wishlist:
            self.store_api.add_to_wishlist(
                self.catalog_offer.namespace,
                self.catalog_offer.id,
                lambda success: self.ui.wishlist_button.setText(self.tr('Remove from wishlist'))
                if success
                else self.ui.wishlist_button.setText('Something went wrong'),
            )
        else:
            self.store_api.remove_from_wishlist(
                self.catalog_offer.namespace,
                self.catalog_offer.id,
                lambda success: self.ui.wishlist_button.setText(self.tr('Add to wishlist'))
                if success
                else self.ui.wishlist_button.setText('Something went wrong'),
            )

    def data_received(self, product: DieselProduct):
        if product.pages:
            product_data: DieselProductDetail = product.pages[0].data
        else:
            product_data: DieselProductDetail = product.data

        self.ui.original_price.setFont(self.font())
        price = self.catalog_offer.price.totalPrice.fmtPrice['originalPrice']
        discount_price = self.catalog_offer.price.totalPrice.fmtPrice['discountPrice']
        if price == '0' or price == 0:
            self.ui.original_price.setText(self.tr('Free'))
        else:
            self.ui.original_price.setText(price)
        if price != discount_price:
            font = self.font()
            font.setStrikeOut(True)
            self.ui.original_price.setFont(font)
            self.ui.discount_price.setText(discount_price if discount_price != '0' else self.tr('Free'))
            self.ui.discount_price.setVisible(True)
        else:
            self.ui.discount_price.setVisible(False)

        requirements = product_data.requirements
        if requirements and requirements.systems:
            for system in requirements.systems:
                req_widget = RequirementsWidget(system, self.requirements_tabs)
                self.requirements_tabs.addTab(req_widget, system.systemType)
            self.ui.requirements_frame.setVisible(True)
        else:
            self.ui.requirements_frame.setVisible(False)

        key_images = self.catalog_offer.keyImages
        img_url = key_images.for_dimensions(self.image.size().width(), self.image.size().height())
        # FIXME: check why there was no tall image
        if img_url:
            self.image.fetchPixmap(img_url.url)

        # self.image_stack.setCurrentIndex(0)
        about = product_data.about
        description = about.description
        description = description.replace('### ', '##### ')
        description = description.replace('## ', '#### ')
        description = description.replace('# ', '### ')
        self.ui.description_field.setMarkdown(description)
        self.ui.developer.setText(about.developerAttribution)
        # try:
        #     if isinstance(aboudeveloper, list):
        #         self.ui.dev.setText(", ".join(self.game.developer))
        #     else:
        #         self.ui.dev.setText(self.game.developer)
        # except KeyError:
        #     pass
        tags = product_data.unmapped['meta'].get('tags', [])
        self.ui.tags.setText(', '.join(tags))

        # clear Layout
        for b in self.ui.social_links.findChildren(SocialButton, options=Qt.FindChildOption.FindDirectChildrenOnly):
            self.ui.social_links_layout.removeWidget(b)
            b.disconnect(b)
            b.deleteLater()

        links = product_data.socialLinks
        link_count = 0
        for name, url in links.items():
            if name == '_type':
                continue
            name = name.replace('link', '').lower()
            if name == 'homepage':
                icn = qta_icon('mdi.web', 'fa5s.globe', scale_factor=1.2)
            elif name == 'title':
                icn = qta_icon('mdi.home-circle', 'fa5s.home', scale_factor=1.2)
            else:
                try:
                    icn = qta_icon(f'mdi.{name}', f'fa5b.{name}', scale_factor=1.2)
                except Exception as e:  # noqa: BLE001
                    logger.error(str(e))
                    continue

            button = SocialButton(icn, url, parent=self.ui.social_links)
            self.ui.social_links_layout.addWidget(button)
            link_count += 1

        self.ui.social_links.setEnabled(bool(link_count))

        self.setEnabled(True)

    # def add_wishlist_items(self, wishlist: List[CatalogGameModel]):
    #     wishlist = wishlist["data"]["Wishlist"]["wishlistItems"]["elements"]
    #     for game in wishlist:
    #         self.wishlist.append(game["offer"]["title"])

    def _app_name(self, offer: CatalogOfferModel) -> str:
        if offer.items:
            return offer.items[0].get('id') or offer.id
        return offer.id

    def is_free(self, offer: CatalogOfferModel) -> bool:
        if offer.price is None or offer.price.totalPrice is None:
            return False
        return offer.price.totalPrice.discountPrice == 0

    def is_owned(self, offer: CatalogOfferModel) -> bool:
        if self.rcore is None:
            return False
        app_name = self._app_name(offer)
        if self.rcore.core().is_installed(app_name):
            return True
        entitlements = self.rcore.core().lgd.entitlements or []
        return any(
            ent.get('namespace') == offer.namespace and ent.get('offerId') == offer.id
            for ent in entitlements
        )

    def is_installed(self, offer: CatalogOfferModel) -> bool:
        if self.rcore is None:
            return False
        return self.rcore.core().is_installed(self._app_name(offer))

    def _update_primary_action(self, offer: CatalogOfferModel):
        if self.is_installed(offer):
            self.ui.store_button.setText(self.tr('In Library'))
            self.ui.status.setText(self.tr('You own this game'))
            self.ui.status.setVisible(True)
            self._primary_mode = 'library'
        elif self.is_owned(offer):
            self.ui.store_button.setText(self.tr('Install'))
            self.ui.status.setText(self.tr('You own this game'))
            self.ui.status.setVisible(True)
            self._primary_mode = 'install'
        elif self.is_free(offer):
            self.ui.store_button.setText(self.tr('Get it free'))
            self.ui.status.setVisible(False)
            self._primary_mode = 'claim'
        else:
            self.ui.store_button.setText(self.tr('Buy on Epic Games Store'))
            self.ui.status.setVisible(False)
            self._primary_mode = 'buy'
        self.ui.store_button.setEnabled(True)

    @Slot()
    def on_primary_action(self):
        offer = self.catalog_offer
        if offer is None or self._primary_mode is None:
            return

        if self._primary_mode == 'library':
            self.open_library.emit()
        elif self._primary_mode == 'install':
            self._install_offer(offer)
        elif self._primary_mode == 'claim':
            self._claim_offer(offer)
        elif self._primary_mode == 'buy':
            self._open_store_page()

    def _open_store_page(self):
        QDesktopServices.openUrl(
            QUrl(f'https://www.epicgames.com/store/{self.store_api.language_code}/p/{self.slug}')
        )

    def _install_offer(self, offer: CatalogOfferModel):
        if self.rcore is None:
            self._open_store_page()
            return
        app_name = self._app_name(offer)
        self.ui.store_button.setEnabled(False)
        self.ui.store_button.setText(self.tr('Installing...'))
        self.rcore.signals().game.install.emit(
            InstallOptionsModel(
                app_name=app_name,
                platform=self.rcore.core().default_platform,
            )
        )
        self.open_library.emit()

    def _claim_offer(self, offer: CatalogOfferModel):
        self.ui.store_button.setEnabled(False)
        self.ui.store_button.setText(self.tr('Claiming...'))
        self.store_api.purchase_free_game(
            offer.namespace,
            offer.id,
            lambda success: self._on_claim_result(offer, success),
        )

    @Slot(bool)
    def _on_claim_result(self, offer: CatalogOfferModel, success: bool):
        if not success:
            self.ui.store_button.setEnabled(True)
            self.ui.store_button.setText(self.tr('Buy on Epic Games Store'))
            self._primary_mode = 'buy'
            self._open_store_page()
            return
        self._update_primary_action(offer)
        self._install_offer(offer)

    def keyPressEvent(self, a0: QKeyEvent):
        if a0.key() == Qt.Key.Key_Escape:
            self.back_clicked.emit()


class SocialButton(QPushButton):
    def __init__(self, icn, url, parent=None):
        super(SocialButton, self).__init__(icn, '', parent=parent)
        self.setFixedSize(36, 36)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.url = url
        self.clicked.connect(self._on_clicked)
        self.setToolTip(url)

    @Slot()
    def _on_clicked(self):
        QDesktopServices.openUrl(QUrl(self.url))


class RequirementsWidget(QWidget, SideTabContents):
    def __init__(self, system: DieselSystemDetail, parent=None):
        super().__init__(parent=parent)
        self.implements_scrollarea = True

        bold_font = self.font()
        bold_font.setBold(True)

        req_layout = QGridLayout(self)
        min_label = QLabel(self.tr('Minimum'), parent=self)
        min_label.setFont(bold_font)
        rec_label = QLabel(self.tr('Recommend'), parent=self)
        rec_label.setFont(bold_font)
        req_layout.addWidget(min_label, 0, 1)
        req_layout.addWidget(rec_label, 0, 2)
        req_layout.setColumnStretch(1, 2)
        req_layout.setColumnStretch(2, 2)
        for i, detail in enumerate(system.details):
            req_layout.addWidget(QLabel(detail.title, parent=self), i + 1, 0)
            min_label = ElideLabel(detail.minimum, parent=self)
            req_layout.addWidget(min_label, i + 1, 1)
            rec_label = ElideLabel(detail.recommended, parent=self)
            req_layout.addWidget(rec_label, i + 1, 2)
        req_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
