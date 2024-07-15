import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Type, Optional, Tuple

logger = logging.getLogger("DieselModels")

# lk: Typing overloads for unimplemented types
DieselSocialLinks = Dict


@dataclass
class DieselSystemDetailItem:
    _type: str = None
    minimum: str = None
    recommended: str = None
    title: str = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselSystemDetailItem"], src: Dict[str, Any]) -> "DieselSystemDetailItem":
        d = src.copy()
        return cls(
            _type=d.pop("_type", ""),
            minimum=d.pop("minimum", ""),
            recommended=d.pop("recommended", ""),
            title=d.pop("title", ""),
            unmapped=d
        )


@dataclass
class DieselSystemDetail:
    _type: str = None
    details: Tuple[DieselSystemDetailItem, ...] = None
    systemType: str = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselSystemDetail"], src: Dict[str, Any]) -> "DieselSystemDetail":
        d = src.copy()
        details = tuple(map(DieselSystemDetailItem.from_dict, d.pop("details", [])))
        return cls(
            _type=d.pop("_type", ""),
            details=details,
            systemType=d.pop("systemType", ""),
            unmapped=d
        )


@dataclass
class DieselSystemDetails:
    _type: str = None
    languages: List[str] = None
    rating: Dict = None
    systems: Tuple[DieselSystemDetail, ...] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselSystemDetails"], src: Dict[str, Any]) -> "DieselSystemDetails":
        d = src.copy()
        systems = tuple(map(DieselSystemDetail.from_dict, d.pop("systems", [])))
        return cls(
            _type=d.pop("_type", ""),
            languages=d.pop("languages", []),
            rating=d.pop("rating", {}),
            systems=systems,
            unmapped=d
        )


@dataclass
class DieselProductAbout:
    _type: str = None
    desciption: str = None
    developerAttribution: str = None
    publisherAttribution: str = None
    shortDescription: str = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselProductAbout"], src: Dict[str, Any]) -> "DieselProductAbout":
        d = src.copy()
        return cls(
            _type=d.pop("_type", ""),
            desciption=d.pop("description", ""),
            developerAttribution=d.pop("developerAttribution", ""),
            publisherAttribution=d.pop("publisherAttribution", ""),
            shortDescription=d.pop("shortDescription", ""),
            unmapped=d
        )


@dataclass
class DieselProductDetail:
    _type: str = None
    about: DieselProductAbout = None
    requirements: DieselSystemDetails = None
    socialLinks: DieselSocialLinks = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselProductDetail"], src: Dict[str, Any]) -> "DieselProductDetail":
        d = src.copy()
        about = DieselProductAbout.from_dict(x) if (x := d.pop("about"), {}) else None
        requirements = DieselSystemDetails.from_dict(x) if (x := d.pop("requirements", {})) else None
        return cls(
            _type=d.pop("_type", ""),
            about=about,
            requirements=requirements,
            socialLinks=d.pop("socialLinks", {}),
            unmapped=d
        )


@dataclass
class DieselProduct:
    _id: str = None
    _images_: List[str] = None
    _locale: str = None
    _slug: str = None
    _title: str = None
    _urlPattern: str = None
    namespace: str = None
    pages: Tuple["DieselProduct", ...] = None
    data: DieselProductDetail = None
    productName: str = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselProduct"], src: Dict[str, Any]) -> "DieselProduct":
        d = src.copy()
        pages = tuple(map(DieselProduct.from_dict, d.pop("pages", [])))
        data = DieselProductDetail.from_dict(x) if (x := d.pop("data", {})) else None
        return cls(
            _id=d.pop("_id", ""),
            _images_=d.pop("_images_", []),
            _locale=d.pop("_locale", ""),
            _slug=d.pop("_slug", ""),
            _title=d.pop("_title", ""),
            _urlPattern=d.pop("_urlPattern", ""),
            namespace=d.pop("namespace", ""),
            pages=pages,
            data=data,
            productName=d.pop("productName", ""),
            unmapped=d
        )
