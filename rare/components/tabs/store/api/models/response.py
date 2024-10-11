import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Type, Tuple

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
    type: str = None
    url: str = None

    def as_dict(self) -> Dict[str, Any]:
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
        return cls(type=d.pop("type", ""), url=d.pop("url", ""))


@dataclass
class KeyImagesModel:
    key_images: Tuple[ImageUrlModel, ...] = None
    tall_types = (
        "DieselGameBoxTall",
        "DieselStoreFrontTall",
        "OfferImageTall",
        "DieselGameBoxLogo",
        "Thumbnail",
        "ProductLogo",
    )
    wide_types = (
        "DieselGameBoxwide",
        "DieselStoreFrontWide",
        "OfferImageWide",
        "DieselGameBox",
        "VaultClosed",
        "ProductLogo",
    )

    def __getitem__(self, item):
        return self.key_images[item]

    def __bool__(self):
        return bool(self.key_images)

    @classmethod
    def from_list(cls: Type["KeyImagesModel"], src: List[Dict]):
        d = src.copy()
        key_images = tuple(map(ImageUrlModel.from_dict, d))
        return cls(key_images=key_images)

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
            logger.error(tuple(map(lambda x: x.as_dict(), self.key_images)))
        else:
            return model


CurrencyModel = Dict
FormattedPriceModel = Dict
LineOffersModel = Dict


@dataclass
class TotalPriceModel:
    discountPrice: int = None
    originalPrice: int = None
    voucherDiscount: int = None
    discount: int = None
    currencyCode: str = None
    currencyInfo: CurrencyModel = None
    fmtPrice: FormattedPriceModel = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["TotalPriceModel"], src: Dict[str, Any]) -> "TotalPriceModel":
        d = src.copy()
        return cls(
            discountPrice=d.pop("discountPrice", 0),
            originalPrice=d.pop("originalPrice", 0),
            voucherDiscount=d.pop("voucherDiscount", 0),
            discount=d.pop("discount", 0),
            currencyCode=d.pop("currencyCode", ""),
            currencyInfo=d.pop("currrencyInfo", {}),
            fmtPrice=d.pop("fmtPrice", {}),
            unmapped=d,
        )


@dataclass
class GetPriceResModel:
    totalPrice: TotalPriceModel = None
    lineOffers: LineOffersModel = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["GetPriceResModel"], src: Dict[str, Any]) -> "GetPriceResModel":
        d = src.copy()
        total_price = TotalPriceModel.from_dict(x) if (x := d.pop("totalPrice", {})) else None
        return cls(totalPrice=total_price, lineOffers=d.pop("lineOffers", {}), unmapped=d)


DiscountSettingModel = Dict


@dataclass
class PromotionalOfferModel:
    startDate: datetime = None
    endDate: datetime = None
    discountSetting: DiscountSettingModel = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["PromotionalOfferModel"], src: Dict[str, Any]) -> "PromotionalOfferModel":
        d = src.copy()
        start_date = parse_date(x) if (x := d.pop("startDate", "")) else None
        end_date = parse_date(x) if (x := d.pop("endDate", "")) else None
        return cls(
            startDate=start_date,
            endDate=end_date,
            discountSetting=d.pop("discountSetting", {}),
            unmapped=d,
        )


@dataclass
class PromotionalOffersModel:
    promotionalOffers: Tuple[PromotionalOfferModel, ...] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_list(cls: Type["PromotionalOffersModel"], src: Dict[str, List]) -> "PromotionalOffersModel":
        d = src.copy()
        promotional_offers = tuple(map(PromotionalOfferModel.from_dict, d.pop("promotionalOffers", [])))
        return cls(promotionalOffers=promotional_offers, unmapped=d)


@dataclass
class PromotionsModel:
    promotionalOffers: Tuple[PromotionalOffersModel, ...] = None
    upcomingPromotionalOffers: Tuple[PromotionalOffersModel, ...] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["PromotionsModel"], src: Dict[str, Any]) -> "PromotionsModel":
        d = src.copy()
        promotional_offers = tuple(map(PromotionalOffersModel.from_list, d.pop("promotionalOffers", [])))
        upcoming_promotional_offers = tuple(
            map(PromotionalOffersModel.from_list, d.pop("upcomingPromotionalOffers", []))
        )
        return cls(
            promotionalOffers=promotional_offers, upcomingPromotionalOffers=upcoming_promotional_offers, unmapped=d
        )


@dataclass
class CatalogOfferModel:
    catalogNs: CatalogNamespaceModel = None
    categories: List[CategoryModel] = None
    customAttributes: List[CustomAttributeModel] = None
    description: str = None
    effectiveDate: datetime = None
    expiryDate: datetime = None
    id: str = None
    isCodeRedemptionOnly: bool = None
    items: List[ItemModel] = None
    keyImages: KeyImagesModel = None
    namespace: str = None
    offerMappings: List[PageSandboxModel] = None
    offerType: str = None
    price: GetPriceResModel = None
    productSlug: str = None
    promotions: PromotionsModel = None
    seller: SellerModel = None
    status: str = None
    tags: List[TagModel] = None
    title: str = None
    url: str = None
    urlSlug: str = None
    viewableDate: datetime = None
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
        return cls(
            catalogNs=d.pop("catalogNs", {}),
            categories=d.pop("categories", []),
            customAttributes=d.pop("customAttributes", []),
            description=d.pop("description", ""),
            effectiveDate=effective_date,
            expiryDate=expiry_date,
            id=d.pop("id", ""),
            isCodeRedemptionOnly=d.pop("isCodeRedemptionOnly", False),
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
            unmapped=d,
        )


@dataclass
class WishlistItemModel:
    created: datetime = None
    id: str = None
    namespace: str = None
    isFirstTime: bool = None
    offerId: str = None
    order: Any = None
    updated: datetime = None
    offer: CatalogOfferModel = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["WishlistItemModel"], src: Dict[str, Any]) -> "WishlistItemModel":
        d = src.copy()
        created = parse_date(x) if (x := d.pop("created", "")) else None
        offer = CatalogOfferModel.from_dict(x) if (x := d.pop("offer", {})) else None
        updated = parse_date(x) if (x := d.pop("updated", "")) else None
        return cls(
            created=created,
            id=d.pop("id", ""),
            namespace=d.pop("namespace", ""),
            isFirstTime=d.pop("isFirstTime", False),
            offerId=d.pop("offerId", ""),
            order=d.pop("order", ""),
            updated=updated,
            offer=offer,
            unmapped=d,
        )


@dataclass
class PagingModel:
    count: int = None
    total: int = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["PagingModel"], src: Dict[str, Any]) -> "PagingModel":
        d = src.copy()
        count = d.pop("count", 0)
        total = d.pop("total", 0)
        return cls(count=count, total=total, unmapped=d)


@dataclass
class SearchStoreModel:
    elements: Tuple[CatalogOfferModel, ...] = None
    paging: PagingModel = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["SearchStoreModel"], src: Dict[str, Any]) -> "SearchStoreModel":
        d = src.copy()
        _elements = d.pop("elements", [])
        elements = tuple(map(CatalogOfferModel.from_dict, _elements))
        paging = PagingModel.from_dict(x) if (x := d.pop("paging", {})) else None
        return cls(elements=elements, paging=paging, unmapped=d)


@dataclass
class CatalogModel:
    searchStore: SearchStoreModel = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["CatalogModel"], src: Dict[str, Any]) -> "CatalogModel":
        d = src.copy()
        search_store = SearchStoreModel.from_dict(x) if (x := d.pop("searchStore", {})) else None
        return cls(searchStore=search_store, unmapped=d)


@dataclass
class WishlistItemsModel:
    elements: Tuple[WishlistItemModel, ...] = None
    paging: PagingModel = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["WishlistItemsModel"], src: Dict[str, Any]) -> "WishlistItemsModel":
        d = src.copy()
        _elements = d.pop("elements", [])
        elements = tuple(map(WishlistItemModel.from_dict, _elements))
        paging = PagingModel.from_dict(x) if (x := d.pop("paging", {})) else None
        return cls(elements=elements, paging=paging, unmapped=d)


@dataclass
class RemoveFromWishlistModel:
    success: bool = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["RemoveFromWishlistModel"], src: Dict[str, Any]) -> "RemoveFromWishlistModel":
        d = src.copy()
        return cls(success=d.pop("success", False), unmapped=d)


@dataclass
class AddToWishlistModel:
    wishlistItem: WishlistItemModel = None
    success: bool = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["AddToWishlistModel"], src: Dict[str, Any]) -> "AddToWishlistModel":
        d = src.copy()
        wishlist_item = WishlistItemModel.from_dict(x) if (x := d.pop("wishlistItem", {})) else None
        return cls(wishlistItem=wishlist_item, success=d.pop("success", False), unmapped=d)


@dataclass
class WishlistModel:
    wishlistItems: WishlistItemsModel = None
    removeFromWishlist: RemoveFromWishlistModel = None
    addToWishlist: AddToWishlistModel = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["WishlistModel"], src: Dict[str, Any]) -> "WishlistModel":
        d = src.copy()
        wishlist_items = WishlistItemsModel.from_dict(x) if (x := d.pop("wishlistItems", {})) else None
        remove_from_wishlist = RemoveFromWishlistModel.from_dict(x) if (x := d.pop("removeFromWishlist", {})) else None
        add_to_wishlist = AddToWishlistModel.from_dict(x) if (x := d.pop("addToWishlist", {})) else None
        return cls(
            wishlistItems=wishlist_items,
            removeFromWishlist=remove_from_wishlist,
            addToWishlist=add_to_wishlist,
            unmapped=d,
        )


ProductModel = Dict


@dataclass
class DataModel:
    product: ProductModel = None
    catalog: CatalogModel = None
    wishlist: WishlistModel = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DataModel"], src: Dict[str, Any]) -> "DataModel":
        d = src.copy()
        catalog = CatalogModel.from_dict(x) if (x := d.pop("Catalog", {})) else None
        wishlist = WishlistModel.from_dict(x) if (x := d.pop("Wishlist", {})) else None
        return cls(product=d.pop("Product", {}), catalog=catalog, wishlist=wishlist, unmapped=d)


@dataclass
class ErrorModel:
    message: str = None
    correlationId: str = None
    serviceResponse: str = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        return f"{self.correlationId} - {self.message}"

    @classmethod
    def from_dict(cls: Type["ErrorModel"], src: Dict[str, Any]) -> "ErrorModel":
        d = src.copy()
        return cls(
            message=d.pop("message", ""),
            correlationId= d.pop("correlationId", ""),
            serviceResponse=d.pop("serviceResponse", ""),
            unmapped=d
        )


@dataclass
class ExtensionsModel:
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["ExtensionsModel"], src: Dict[str, Any]) -> "ExtensionsModel":
        d = src.copy()
        return cls(unmapped=d)


@dataclass
class ResponseModel:
    data: DataModel = None
    errors: Tuple[ErrorModel, ...] = None
    extensions: ExtensionsModel = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["ResponseModel"], src: Dict[str, Any]) -> "ResponseModel":
        d = src.copy()
        data = DataModel.from_dict(x) if (x := d.pop("data", {})) else None
        _errors = d.pop("errors", [])
        errors = tuple(map(ErrorModel.from_dict, _errors))
        extensions = ExtensionsModel.from_dict(x) if (x := d.pop("extensions", {})) else None
        return cls(data=data, errors=errors, extensions=extensions, unmapped=d)
