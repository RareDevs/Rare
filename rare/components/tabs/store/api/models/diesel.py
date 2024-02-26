import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Type, Optional

logger = logging.getLogger("DieselModels")

# lk: Typing overloads for unimplemented types
DieselSocialLinks = Dict


@dataclass
class DieselSystemDetailItem:
    _type: Optional[str] = None
    minimum: Optional[str] = None
    recommended: Optional[str] = None
    title: Optional[str] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselSystemDetailItem"], src: Dict[str, Any]) -> "DieselSystemDetailItem":
        d = src.copy()
        tmp = cls(
            _type=d.pop("_type", ""),
            minimum=d.pop("minimum", ""),
            recommended=d.pop("recommended", ""),
            title=d.pop("title", ""),
        )
        tmp.unmapped = d
        return tmp


@dataclass
class DieselSystemDetail:
    _type: Optional[str] = None
    details: Optional[List[DieselSystemDetailItem]] = None
    systemType: Optional[str] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselSystemDetail"], src: Dict[str, Any]) -> "DieselSystemDetail":
        d = src.copy()
        _details = d.pop("details", [])
        details = [] if _details else None
        for item in _details:
            detail = DieselSystemDetailItem.from_dict(item)
            details.append(detail)
        tmp = cls(
            _type=d.pop("_type", ""),
            details=details,
            systemType=d.pop("systemType", ""),
        )
        tmp.unmapped = d
        return tmp


@dataclass
class DieselSystemDetails:
    _type: Optional[str] = None
    languages: Optional[List[str]] = None
    rating: Optional[Dict] = None
    systems: Optional[List[DieselSystemDetail]] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselSystemDetails"], src: Dict[str, Any]) -> "DieselSystemDetails":
        d = src.copy()
        _systems = d.pop("systems", [])
        systems = [] if _systems else None
        for item in _systems:
            system = DieselSystemDetail.from_dict(item)
            systems.append(system)
        tmp = cls(
            _type=d.pop("_type", ""),
            languages=d.pop("languages", []),
            rating=d.pop("rating", {}),
            systems=systems,
        )
        tmp.unmapped = d
        return tmp


@dataclass
class DieselProductAbout:
    _type: Optional[str] = None
    desciption: Optional[str] = None
    developerAttribution: Optional[str] = None
    publisherAttribution: Optional[str] = None
    shortDescription: Optional[str] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselProductAbout"], src: Dict[str, Any]) -> "DieselProductAbout":
        d = src.copy()
        tmp = cls(
            _type=d.pop("_type", ""),
            desciption=d.pop("description", ""),
            developerAttribution=d.pop("developerAttribution", ""),
            publisherAttribution=d.pop("publisherAttribution", ""),
            shortDescription=d.pop("shortDescription", ""),
        )
        tmp.unmapped = d
        return tmp


@dataclass
class DieselProductDetail:
    _type: Optional[str] = None
    about: Optional[DieselProductAbout] = None
    requirements: Optional[DieselSystemDetails] = None
    socialLinks: Optional[DieselSocialLinks] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselProductDetail"], src: Dict[str, Any]) -> "DieselProductDetail":
        d = src.copy()
        about = DieselProductAbout.from_dict(x) if (x := d.pop("about"), {}) else None
        requirements = DieselSystemDetails.from_dict(x) if (x := d.pop("requirements", {})) else None
        tmp = cls(
            _type=d.pop("_type", ""),
            about=about,
            requirements=requirements,
            socialLinks=d.pop("socialLinks", {}),
        )
        tmp.unmapped = d
        return tmp


@dataclass
class DieselProduct:
    _id: Optional[str] = None
    _images_: Optional[List[str]] = None
    _locale: Optional[str] = None
    _slug: Optional[str] = None
    _title: Optional[str] = None
    _urlPattern: Optional[str] = None
    namespace: Optional[str] = None
    pages: Optional[List["DieselProduct"]] = None
    data: Optional[DieselProductDetail] = None
    productName: Optional[str] = None
    unmapped: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls: Type["DieselProduct"], src: Dict[str, Any]) -> "DieselProduct":
        d = src.copy()
        _pages = d.pop("pages", [])
        pages = [] if _pages else None
        for item in _pages:
            page = DieselProduct.from_dict(item)
            pages.append(page)
        data = DieselProductDetail.from_dict(x) if (x := d.pop("data", {})) else None
        tmp = cls(
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
        )
        tmp.unmapped = d
        return tmp
