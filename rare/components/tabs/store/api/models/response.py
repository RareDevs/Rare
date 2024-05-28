import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Type, Optional, Tuple

from .utils import parse_date

logger = logging.getLogger("StoreApiModels")

# lk: Typing overloads for unimplemented types
DieselSocialLinks = Dict

CatalogNamespaceModel = Dict
CategoryModel = Dict
CustomAttributeModel = Dict
ItemModel = Dict
SellerModel = Dict
PageSandboxModel = Dict
TagModel = Dict


@dataclass
class ImageUrlModel:
    type: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        tmp: Dict[str, Any] = {}
        tmp.update({})
        if self.type is not None:
            tmp["type"] = self.type
        if self.url is not None:
            tmp["url"] = self.url
        return tmp

    @classmethod
    def from_dict(cls: Type["ImageUrlModel"], src: Dict[str, Any]) -> "ImageUrlModel":
        d = src.copy()
        type = d.pop("type", None)
        url = d.pop("url", None)
        tmp = cls(type=type, url=url)
        return tmp


@dataclass
class KeyImagesModel:
    key_images: Optional[List[ImageUrlModel]] = None
    tall_types = ("DieselGameBoxTall", "DieselStoreFrontTall", "OfferImageTall", "DieselGameBoxLogo", "Thumbnail", "ProductLogo")
    wide_types = ("DieselGameBoxwide", "DieselStoreFrontWide", "OfferImageWide", "DieselGameBox", "VaultClosed", "ProductLogo")

    def __getitem__(self, item):
        return self.key_images[item]

    def __bool__(self):
        return bool(self.key_images)

    def to_list(self) -> List[Dict[str, Any]]:
        items: Optional[List[Dict[str, Any]]] = None
        if self.key_images is not None:
            items = []
            for image_url in self.key_images:
                item = image_url.to_dict()
                items.append(item)
        return items

    @classmethod
    def from_list(cls: Type["KeyImagesModel"], src: List[Dict]):
        d = src.copy()
        key_images = []
        for item in d:
            image_url = ImageUrlModel.from_dict(item)
            key_images.append(image_url)
        tmp = cls(key_images)
        return tmp

    def available_tall(self) -> List[ImageUrlModel]:
        tall_images = filter(lambda img: img.type in KeyImagesModel.tall_types, self.key_images)
        tall_images = sorted(tall_images, key=lambda x: KeyImagesModel.tall_types.index(x.type))
        return tall_images

    def available_wide(self) -> List[ImageUrlModel]:
        wide_images = filter(lambda img: img.type in KeyImagesModel.wide_types, self.key_images)
        wide_images = sorted(wide_images, key=lambda x: KeyImagesModel.wide_types.index(x.type))
        return wide_images

    def for_dimensions(self, w: int, h: int) -> ImageUrlModel:
        try:
            if w > h:
                model = self.available_wide()[0]
            else:
                model = self.available_tall()[0]
            _ = model.url
        except Exception as e:
            logger.error(e)
            logger.error(self.to_list())
        else:
            return model


CurrencyModel = Dict
FormattedPriceModel = Dict
LineOffersModel = Dict


@dataclass
class TotalPriceModel:
    discountPrice: Optional[int] = None
    originalPrice: Optional[int] = None
    voucherDiscount: Optional[int] = None
    discount: Optional[int] = None
    currencyCode: Optional[str] = None
    currencyInfo: Optional[CurrencyModel] = None
    fmtPrice: Optional[FormattedPriceModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["TotalPriceModel"], src: Dict[str, Any]) -> "TotalPriceModel":
        d = src.copy()
        tmp = cls(
            discountPrice=d.pop("discountPrice", None),
            originalPrice=d.pop("originalPrice", None),
            voucherDiscount=d.pop("voucherDiscount", None),
            discount=d.pop("discount", None),
            currencyCode=d.pop("currencyCode", None),
            currencyInfo=d.pop("currrencyInfo", {}),
            fmtPrice=d.pop("fmtPrice", {}),
        )
        tmp.unmapped = d
        return tmp


@dataclass
class GetPriceResModel:
    totalPrice: Optional[TotalPriceModel] = None
    lineOffers: Optional[LineOffersModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["GetPriceResModel"], src: Dict[str, Any]) -> "GetPriceResModel":
        d = src.copy()
        total_price = TotalPriceModel.from_dict(x) if (x := d.pop("totalPrice", {})) else None
        tmp = cls(totalPrice=total_price, lineOffers=d.pop("lineOffers", {}))
        tmp.unmapped = d
        return tmp


DiscountSettingModel = Dict


@dataclass
class PromotionalOfferModel:
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    discountSetting: Optional[DiscountSettingModel] = None

    @classmethod
    def from_dict(cls: Type["PromotionalOfferModel"], src: Dict[str, Any]) -> "PromotionalOfferModel":
        d = src.copy()
        start_date = parse_date(x) if (x := d.pop("startDate", "")) else None
        end_date = parse_date(x) if (x := d.pop("endDate", "")) else None
        tmp = cls(startDate=start_date, endDate=end_date, discountSetting=d.pop("discountSetting", {}))
        tmp.unmapped = d
        return tmp


@dataclass
class PromotionalOffersModel:
    promotionalOffers: Optional[Tuple[PromotionalOfferModel]] = None

    @classmethod
    def from_list(cls: Type["PromotionalOffersModel"], src: Dict[str, List]) -> "PromotionalOffersModel":
        d = src.copy()
        promotional_offers = (
            tuple([PromotionalOfferModel.from_dict(y) for y in x]) if (x := d.pop("promotionalOffers", [])) else None
        )
        tmp = cls(promotionalOffers=promotional_offers)
        tmp.unmapped = d
        return tmp


@dataclass
class PromotionsModel:
    promotionalOffers: Optional[Tuple[PromotionalOffersModel]] = None
    upcomingPromotionalOffers: Optional[Tuple[PromotionalOffersModel]] = None

    @classmethod
    def from_dict(cls: Type["PromotionsModel"], src: Dict[str, Any]) -> "PromotionsModel":
        d = src.copy()
        promotional_offers = (
            tuple([PromotionalOffersModel.from_list(y) for y in x]) if (x := d.pop("promotionalOffers", [])) else None
        )
        upcoming_promotional_offers = (
            tuple([PromotionalOffersModel.from_list(y) for y in x])
            if (x := d.pop("upcomingPromotionalOffers", []))
            else None
        )
        tmp = cls(promotionalOffers=promotional_offers, upcomingPromotionalOffers=upcoming_promotional_offers)
        tmp.unmapped = d
        return tmp


@dataclass
class CatalogOfferModel:
    catalogNs: Optional[CatalogNamespaceModel] = None
    categories: Optional[List[CategoryModel]] = None
    customAttributes: Optional[List[CustomAttributeModel]] = None
    description: Optional[str] = None
    effectiveDate: Optional[datetime] = None
    expiryDate: Optional[datetime] = None
    id: Optional[str] = None
    isCodeRedemptionOnly: Optional[bool] = None
    items: Optional[List[ItemModel]] = None
    keyImages: Optional[KeyImagesModel] = None
    namespace: Optional[str] = None
    offerMappings: Optional[List[PageSandboxModel]] = None
    offerType: Optional[str] = None
    price: Optional[GetPriceResModel] = None
    productSlug: Optional[str] = None
    promotions: Optional[PromotionsModel] = None
    seller: Optional[SellerModel] = None
    status: Optional[str] = None
    tags: Optional[List[TagModel]] = None
    title: Optional[str] = None
    url: Optional[str] = None
    urlSlug: Optional[str] = None
    viewableDate: Optional[datetime] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["CatalogOfferModel"], src: Dict[str, Any]) -> "CatalogOfferModel":
        d = src.copy()
        effective_date = parse_date(x) if (x := d.pop("effectiveDate", "")) else None
        expiry_date = parse_date(x) if (x := d.pop("expiryDate", "")) else None
        key_images = KeyImagesModel.from_list(d.pop("keyImages", []))
        price = GetPriceResModel.from_dict(x) if (x := d.pop("price", {})) else None
        promotions = PromotionsModel.from_dict(x) if (x := d.pop("promotions", {})) else None
        viewable_date = parse_date(x) if (x := d.pop("viewableDate", "")) else None
        tmp = cls(
            catalogNs=d.pop("catalogNs", {}),
            categories=d.pop("categories", []),
            customAttributes=d.pop("customAttributes", []),
            description=d.pop("description", ""),
            effectiveDate=effective_date,
            expiryDate=expiry_date,
            id=d.pop("id", ""),
            isCodeRedemptionOnly=d.pop("isCodeRedemptionOnly", None),
            items=d.pop("items", []),
            keyImages=key_images,
            namespace=d.pop("namespace", ""),
            offerMappings=d.pop("offerMappings", []),
            offerType=d.pop("offerType", ""),
            price=price,
            productSlug=d.pop("productSlug", ""),
            promotions=promotions,
            seller=d.pop("seller", {}),
            status=d.pop("status", ""),
            tags=d.pop("tags", []),
            title=d.pop("title", ""),
            url=d.pop("url", ""),
            urlSlug=d.pop("urlSlug", ""),
            viewableDate=viewable_date,
        )
        tmp.unmapped = d
        return tmp


@dataclass
class WishlistItemModel:
    created: Optional[datetime] = None
    id: Optional[str] = None
    namespace: Optional[str] = None
    isFirstTime: Optional[bool] = None
    offerId: Optional[str] = None
    order: Optional[Any] = None
    updated: Optional[datetime] = None
    offer: Optional[CatalogOfferModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["WishlistItemModel"], src: Dict[str, Any]) -> "WishlistItemModel":
        d = src.copy()
        created = parse_date(x) if (x := d.pop("created", "")) else None
        offer = CatalogOfferModel.from_dict(x) if (x := d.pop("offer", {})) else None
        updated = parse_date(x) if (x := d.pop("updated", "")) else None
        tmp = cls(
            created=created,
            id=d.pop("id", ""),
            namespace=d.pop("namespace", ""),
            isFirstTime=d.pop("isFirstTime", None),
            offerId=d.pop("offerId", ""),
            order=d.pop("order", ""),
            updated=updated,
            offer=offer,
        )
        tmp.unmapped = d
        return tmp


@dataclass
class PagingModel:
    count: Optional[int] = None
    total: Optional[int] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["PagingModel"], src: Dict[str, Any]) -> "PagingModel":
        d = src.copy()
        count = d.pop("count", None)
        total = d.pop("total", None)
        tmp = cls(count=count, total=total)
        tmp.unmapped = d
        return tmp


@dataclass
class SearchStoreModel:
    elements: Optional[List[CatalogOfferModel]] = None
    paging: Optional[PagingModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["SearchStoreModel"], src: Dict[str, Any]) -> "SearchStoreModel":
        d = src.copy()
        _elements = d.pop("elements", [])
        elements = [] if _elements else None
        for item in _elements:
            elem = CatalogOfferModel.from_dict(item)
            elements.append(elem)
        paging = PagingModel.from_dict(x) if (x := d.pop("paging", {})) else None
        tmp = cls(elements=elements, paging=paging)
        tmp.unmapped = d
        return tmp


@dataclass
class CatalogModel:
    searchStore: Optional[SearchStoreModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["CatalogModel"], src: Dict[str, Any]) -> "CatalogModel":
        d = src.copy()
        search_store = SearchStoreModel.from_dict(x) if (x := d.pop("searchStore", {})) else None
        tmp = cls(searchStore=search_store)
        tmp.unmapped = d
        return tmp


@dataclass
class WishlistItemsModel:
    elements: Optional[List[WishlistItemModel]] = None
    paging: Optional[PagingModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["WishlistItemsModel"], src: Dict[str, Any]) -> "WishlistItemsModel":
        d = src.copy()
        _elements = d.pop("elements", [])
        elements = [] if _elements else None
        for item in _elements:
            elem = WishlistItemModel.from_dict(item)
            elements.append(elem)
        paging = PagingModel.from_dict(x) if (x := d.pop("paging", {})) else None
        tmp = cls(elements=elements, paging=paging)
        tmp.unmapped = d
        return tmp


@dataclass
class RemoveFromWishlistModel:
    success: Optional[bool] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["RemoveFromWishlistModel"], src: Dict[str, Any]) -> "RemoveFromWishlistModel":
        d = src.copy()
        tmp = cls(success=d.pop("success", None))
        tmp.unmapped = d
        return tmp


@dataclass
class AddToWishlistModel:
    wishlistItem: Optional[WishlistItemModel] = None
    success: Optional[bool] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["AddToWishlistModel"], src: Dict[str, Any]) -> "AddToWishlistModel":
        d = src.copy()
        wishlist_item = WishlistItemModel.from_dict(x) if (x := d.pop("wishlistItem", {})) else None
        tmp = cls(wishlistItem=wishlist_item, success=d.pop("success", None))
        tmp.unmapped = d
        return tmp


@dataclass
class WishlistModel:
    wishlistItems: Optional[WishlistItemsModel] = None
    removeFromWishlist: Optional[RemoveFromWishlistModel] = None
    addToWishlist: Optional[AddToWishlistModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["WishlistModel"], src: Dict[str, Any]) -> "WishlistModel":
        d = src.copy()
        wishlist_items = WishlistItemsModel.from_dict(x) if (x := d.pop("wishlistItems", {})) else None
        remove_from_wishlist = RemoveFromWishlistModel.from_dict(x) if (x := d.pop("removeFromWishlist", {})) else None
        add_to_wishlist = AddToWishlistModel.from_dict(x) if (x := d.pop("addToWishlist", {})) else None
        tmp = cls(
            wishlistItems=wishlist_items, removeFromWishlist=remove_from_wishlist, addToWishlist=add_to_wishlist
        )
        tmp.unmapped = d
        return tmp


ProductModel = Dict


@dataclass
class DataModel:
    product: Optional[ProductModel] = None
    catalog: Optional[CatalogModel] = None
    wishlist: Optional[WishlistModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DataModel"], src: Dict[str, Any]) -> "DataModel":
        d = src.copy()
        catalog = CatalogModel.from_dict(x) if (x := d.pop("Catalog", {})) else None
        wishlist = WishlistModel.from_dict(x) if (x := d.pop("Wishlist", {})) else None
        tmp = cls(product=d.pop("Product", {}), catalog=catalog, wishlist=wishlist)
        tmp.unmapped = d
        return tmp


@dataclass
class ErrorModel:
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["ErrorModel"], src: Dict[str, Any]) -> "ErrorModel":
        d = src.copy()
        tmp = cls()
        tmp.unmapped = d
        return tmp


@dataclass
class ExtensionsModel:
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["ExtensionsModel"], src: Dict[str, Any]) -> "ExtensionsModel":
        d = src.copy()
        tmp = cls()
        tmp.unmapped = d
        return tmp


@dataclass
class ResponseModel:
    data: Optional[DataModel] = None
    errors: Optional[List[ErrorModel]] = None
    extensions: Optional[ExtensionsModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["ResponseModel"], src: Dict[str, Any]) -> "ResponseModel":
        d = src.copy()
        data = DataModel.from_dict(x) if (x := d.pop("data", {})) else None
        _errors = d.pop("errors", [])
        errors = [] if _errors else None
        for item in _errors:
            error = ErrorModel.from_dict(item)
            errors.append(error)
        extensions = ExtensionsModel.from_dict(x) if (x := d.pop("extensions", {})) else None
        tmp = cls(data=data, errors=errors, extensions=extensions)
        tmp.unmapped = d
        return tmp
