from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class SearchDateRange:
    start_date: datetime = datetime(year=1990, month=1, day=1, tzinfo=timezone.utc)
    end_date: datetime = datetime.now(timezone.utc)

    def __str__(self):
        def fmt_date(date: datetime) -> str:
            # lk: The formatting accepted by the GraphQL API is either '%Y-%m-%dT%H:%M:%S.000Z' or '%Y-%m-%d'
            return datetime.strftime(date, '%Y-%m-%dT%H:%M:%S.000Z')
        return f"[{fmt_date(self.start_date)},{fmt_date(self.end_date)}]"


@dataclass
class SearchStoreQuery:
    country: str = "US"
    category: str = "games/edition/base|bundles/games|editors|software/edition/base"
    count: int = 30
    keywords: str = ""
    language: str = "en"
    namespace: str = ""
    with_mapping: bool = True
    item_ns: str = ""
    sort_by: str = "releaseDate"
    sort_dir: str = "DESC"
    start: int = 0
    tag: List[str] = ""
    release_date: SearchDateRange = field(default_factory=SearchDateRange)
    with_price: bool = True
    with_promotions: bool = True
    price_range: str = ""
    free_game: bool = None
    on_sale: bool = None
    effective_date: SearchDateRange = field(default_factory=SearchDateRange)

    def __post_init__(self):
        self.locale = f"{self.language}-{self.country}"

    def to_dict(self):
        payload = {
            "allowCountries": self.country,
            "category": self.category,
            "count": self.count,
            "country": self.country,
            "keywords": self.keywords,
            "locale": self.locale,
            "namespace": self.namespace,
            "withMapping": self.with_mapping,
            "itemNs": self.item_ns,
            "sortBy": self.sort_by,
            "sortDir": self.sort_dir,
            "start": self.start,
            "tag": self.tag,
            "releaseDate": str(self.release_date),
            "withPrice": self.with_price,
            "withPromotions": self.with_promotions,
            "priceRange": self.price_range,
            "freeGame": self.free_game,
            "onSale": self.on_sale,
            "effectiveDate": str(self.effective_date),
        }
        # payload.pop("withPromotions")
        payload.pop("onSale")
        if self.price_range == "free":
            payload["freeGame"] = True
            payload.pop("priceRange")
        elif self.price_range.startswith("<price>"):
            payload["priceRange"] = self.price_range.replace("<price>", "")
        if self.on_sale:
            payload["onSale"] = True

        if self.price_range:
            payload["effectiveDate"] = self.effective_date
        else:
            payload.pop("priceRange")
        return payload
