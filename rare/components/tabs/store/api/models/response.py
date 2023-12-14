import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Type, Optional

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
PromotionsModel = Dict


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
        tmp = cls(
            type=type,
            url=url,
        )
        return tmp


@dataclass
class KeyImagesModel:
    key_images: Optional[List[ImageUrlModel]] = None

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
        tall_types = [
            "DieselStoreFrontTall",
            "OfferImageTall",
            "Thumbnail",
            "ProductLogo",
            "DieselGameBoxLogo",
        ]
        tall_images = filter(lambda img: img.type in tall_types, self.key_images)
        tall_images = sorted(tall_images, key=lambda x: tall_types.index(x.type))
        return tall_images

    def available_wide(self) -> List[ImageUrlModel]:
        wide_types = ["DieselStoreFrontWide", "OfferImageWide", "VaultClosed", "ProductLogo"]
        wide_images = filter(lambda img: img.type in wide_types, self.key_images)
        wide_images = sorted(wide_images, key=lambda x: wide_types.index(x.type))
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


TotalPriceModel = Dict
FmtPriceModel = Dict
LineOffersModel = Dict


@dataclass
class GetPriceResModel:
    total_price: Optional[TotalPriceModel] = None
    fmt_price: Optional[FmtPriceModel] = None
    line_offers: Optional[LineOffersModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["GetPriceResModel"], src: Dict[str, Any]) -> "GetPriceResModel":
        d = src.copy()
        tmp = cls(
            total_price=d.pop("totalPrice", {}),
            fmt_price=d.pop("fmtPrice", {}),
            line_offers=d.pop("lineOffers", {}),
        )
        tmp.unmapped = d
        return tmp


@dataclass
class CatalogOfferModel:
    catalog_ns: Optional[CatalogNamespaceModel] = None
    categories: Optional[List[CategoryModel]] = None
    custom_attributes: Optional[List[CustomAttributeModel]] = None
    description: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    id: Optional[str] = None
    is_code_redemption_only: Optional[bool] = None
    items: Optional[List[ItemModel]] = None
    key_images: Optional[KeyImagesModel] = None
    namespace: Optional[str] = None
    offer_mappings: Optional[List[PageSandboxModel]] = None
    offer_type: Optional[str] = None
    price: Optional[GetPriceResModel] = None
    product_slug: Optional[str] = None
    promotions: Optional[PromotionsModel] = None
    seller: Optional[SellerModel] = None
    status: Optional[str] = None
    tags: Optional[List[TagModel]] = None
    title: Optional[str] = None
    url: Optional[str] = None
    url_slug: Optional[str] = None
    viewable_date: Optional[datetime] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["CatalogOfferModel"], src: Dict[str, Any]) -> "CatalogOfferModel":
        d = src.copy()
        effective_date = parse_date(x) if (x := d.pop("effectiveDate", "")) else None
        expiry_date = parse_date(x) if (x := d.pop("expiryDate", "")) else None
        key_images = KeyImagesModel.from_list(d.pop("keyImages", []))
        price = GetPriceResModel.from_dict(x) if (x := d.pop("price", {})) else None
        viewable_date = parse_date(x) if (x := d.pop("viewableDate", "")) else None
        tmp = cls(
            catalog_ns=d.pop("catalogNs", {}),
            categories=d.pop("categories", []),
            custom_attributes=d.pop("customAttributes", []),
            description=d.pop("description", ""),
            effective_date=effective_date,
            expiry_date=expiry_date,
            id=d.pop("id", ""),
            is_code_redemption_only=d.pop("isCodeRedemptionOnly", None),
            items=d.pop("items", []),
            key_images=key_images,
            namespace=d.pop("namespace", ""),
            offer_mappings=d.pop("offerMappings", []),
            offer_type=d.pop("offerType", ""),
            price=price,
            product_slug=d.pop("productSlug", ""),
            promotions=d.pop("promotions", {}),
            seller=d.pop("seller", {}),
            status=d.pop("status", ""),
            tags=d.pop("tags", []),
            title=d.pop("title", ""),
            url=d.pop("url", ""),
            url_slug=d.pop("urlSlug", ""),
            viewable_date=viewable_date,
        )
        tmp.unmapped = d
        return tmp


@dataclass
class WishlistItemModel:
    created: Optional[datetime] = None
    id: Optional[str] = None
    namespace: Optional[str] = None
    is_first_time: Optional[bool] = None
    offer_id: Optional[str] = None
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
            is_first_time=d.pop("isFirstTime", None),
            offer_id=d.pop("offerId", ""),
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
        tmp = cls(
            count=count,
            total=total,
        )
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
        tmp = cls(
            elements=elements,
            paging=paging,
        )
        tmp.unmapped = d
        return tmp


@dataclass
class CatalogModel:
    search_store: Optional[SearchStoreModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["CatalogModel"], src: Dict[str, Any]) -> "CatalogModel":
        d = src.copy()
        search_store = SearchStoreModel.from_dict(x) if (x := d.pop("searchStore", {})) else None
        tmp = cls(
            search_store=search_store,
        )
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
        tmp = cls(
            elements=elements,
            paging=paging,
        )
        tmp.unmapped = d
        return tmp


@dataclass
class RemoveFromWishlistModel:
    success: Optional[bool] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["RemoveFromWishlistModel"], src: Dict[str, Any]) -> "RemoveFromWishlistModel":
        d = src.copy()
        tmp = cls(
            success=d.pop("success", None),
        )
        tmp.unmapped = d
        return tmp


@dataclass
class AddToWishlistModel:
    wishlist_item: Optional[WishlistItemModel] = None
    success: Optional[bool] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["AddToWishlistModel"], src: Dict[str, Any]) -> "AddToWishlistModel":
        d = src.copy()
        wishlist_item = WishlistItemModel.from_dict(x) if (x := d.pop("wishlistItem", {})) else None
        tmp = cls(
            wishlist_item=wishlist_item,
            success=d.pop("success", None),
        )
        tmp.unmapped = d
        return tmp


@dataclass
class WishlistModel:
    wishlist_items: Optional[WishlistItemsModel] = None
    remove_from_wishlist: Optional[RemoveFromWishlistModel] = None
    add_to_wishlist: Optional[AddToWishlistModel] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["WishlistModel"], src: Dict[str, Any]) -> "WishlistModel":
        d = src.copy()
        wishlist_items = WishlistItemsModel.from_dict(x) if (x := d.pop("wishlistItems", {})) else None
        remove_from_wishlist = (
            RemoveFromWishlistModel.from_dict(x) if (x := d.pop("removeFromWishlist", {})) else None
        )
        add_to_wishlist = AddToWishlistModel.from_dict(x) if (x := d.pop("addToWishlist", {})) else None
        tmp = cls(
            wishlist_items=wishlist_items,
            remove_from_wishlist=remove_from_wishlist,
            add_to_wishlist=add_to_wishlist,
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