from PySide6.QtCore import QObject


# Class to use QObject.tr()
class Constants(QObject):
    def __init__(self):
        super(Constants, self).__init__()
        self.categories = sorted(
            [
                (self.tr('Action'), '1216'),
                (self.tr('Adventure'), '1117'),
                (self.tr('Puzzle'), '1298'),
                (self.tr('Open world'), '1307'),
                (self.tr('Racing'), '1212'),
                (self.tr('RPG'), '1367'),
                (self.tr('Shooter'), '1210'),
                (self.tr('Strategy'), '1115'),
                (self.tr('Survival'), '1080'),
                (self.tr('First Person'), '1294'),
                (self.tr('Indie'), '1263'),
                (self.tr('Simulation'), '1393'),
                (self.tr('Sport'), '1283'),
            ],
            key=lambda x: x[0],
        )

        self.platforms = [
            ('MacOS', '9548'),
            ('Windows', '9547'),
        ]
        self.others = [
            (self.tr('Single player'), '1370'),
            (self.tr('Multiplayer'), '1203'),
            (self.tr('Controller'), '9549'),
            (self.tr('Co-op'), '1264'),
        ]

        self.types = [
            (self.tr('Editor'), 'editors'),
            (self.tr('Game'), 'games/edition/base'),
            (self.tr('Bundle'), 'bundles/games'),
            (self.tr('Add-on'), 'addons'),
            (self.tr('Apps'), 'software/edition/base'),
        ]


__Image = """
type
url
alt
"""

__StorePageMapping = """
cmsSlug
offerId
prePurchaseOfferId
"""

__PageSandboxModel = f"""
pageSlug
pageType
productId
sandboxId
createdDate
updatedDate
deletedDate
mappings {{
  {__StorePageMapping}
}}
"""

__CatalogNamespace = f"""
parent
displayName
store
home: mappings(pageType: "productHome") {{
  {__PageSandboxModel}
}}
addons: mappings(pageType: "addon--cms-hybrid") {{
  {__PageSandboxModel}
}}
offers: mappings(pageType: "offer") {{
  {__PageSandboxModel}
}}
"""

__CatalogItem = """
id
namespace
"""

__GetPriceRes = """
  totalPrice {
    discountPrice
    originalPrice
    voucherDiscount
    discount
    currencyCode
    currencyInfo {
      decimals
      symbol
    }
    fmtPrice(locale: $locale) {
      originalPrice
      discountPrice
      intermediatePrice
    }
  }
  lineOffers {
    appliedRules {
      id
      endDate
      discountSetting {
        discountType
      }
    }
  }
"""

__Promotions = """
promotionalOffers {
    promotionalOffers {
        startDate
        endDate
        discountSetting {
            discountType
            discountPercentage
        }
    }
}
upcomingPromotionalOffers {
    promotionalOffers {
        startDate
        endDate
        discountSetting {
            discountType
            discountPercentage
        }
    }
}
"""

__CatalogOffer = f"""
title
id
namespace
offerType
expiryDate
status
isCodeRedemptionOnly
description
effectiveDate
keyImages {{
    {__Image}
}}
currentPrice
seller {{
  id
  name
}}
productSlug
urlSlug
url
tags {{
  id
  name
  groupName
}}
items {{
    {__CatalogItem}
}}
customAttributes {{
  key
  value
}}
categories {{
  path
}}
catalogNs @include(if: $withMapping) {{
    {__CatalogNamespace}
}}
offerMappings @include(if: $withMapping) {{
    {__PageSandboxModel}
}}
price(country: $country) @include(if: $withPrice) {{
    {__GetPriceRes}
}}
promotions(category: $category) @include(if: $withPromotions) {{
    {__Promotions}
}}
"""

__Pagination = """
count
total
"""

SEARCH_STORE_QUERY = f"""
query searchStoreQuery(
  $allowCountries: String
  $category: String
  $count: Int
  $country: String!
  $keywords: String
  $locale: String
  $namespace: String
  $withMapping: Boolean = false
  $itemNs: String
  $sortBy: String
  $sortDir: String
  $start: Int
  $tag: String
  $releaseDate: String
  $withPrice: Boolean = false
  $withPromotions: Boolean = false
  $priceRange: String
  $freeGame: Boolean
  $onSale: Boolean
  $effectiveDate: String
) {{
  Catalog {{
    searchStore(
      allowCountries: $allowCountries
      category: $category
      count: $count
      country: $country
      keywords: $keywords
      locale: $locale
      namespace: $namespace
      itemNs: $itemNs
      sortBy: $sortBy
      sortDir: $sortDir
      releaseDate: $releaseDate
      start: $start
      tag: $tag
      priceRange: $priceRange
      freeGame: $freeGame
      onSale: $onSale
      effectiveDate: $effectiveDate
    ) {{
      elements {{
        {__CatalogOffer}
      }}
      paging {{
        {__Pagination}
      }}
    }}
  }}
}}
"""

__WISHLIST_ITEM = f"""
id
order
created
offerId
updated
namespace
isFirstTime
offer(locale: $locale) {{
  {__CatalogOffer}
}}
"""

WISHLIST_QUERY = f"""
query wishlistQuery(
  $country: String!
  $locale: String
  $category: String
  $withMapping: Boolean = false
  $withPrice: Boolean = false
  $withPromotions: Boolean = false
) {{
  Wishlist {{
    wishlistItems {{
      elements {{
        {__WISHLIST_ITEM}
      }}
    }}
  }}
}}
"""

WISHLIST_ADD_QUERY = f"""
mutation addWishlistMutation(
  $namespace: String!
  $offerId: String!
  $country: String!
  $locale: String
  $category: String
  $withMapping: Boolean = false
  $withPrice: Boolean = false
  $withPromotions: Boolean = false
) {{
  Wishlist {{
    addToWishlist(
      namespace: $namespace
      offerId: $offerId
    ) {{
      wishlistItem {{
        {__WISHLIST_ITEM}
      }}
      success
    }}
  }}
}}
"""

WISHLIST_REMOVE_QUERY = """
mutation removeFromWishlistMutation(
  $namespace: String!
  $offerId: String!
  $operation: RemoveOperation!
) {
  Wishlist {
    removeFromWishlist(
      namespace: $namespace
      offerId: $offerId
      operation: $operation
    ) {
      success
    }
  }
}
"""

COUPONS_QUERY = """
query getCoupons(
  $currencyCountry: String!
  $identityId: String!
  $locale: String
) {
  CodeRedemption {
    coupons(
      currencyCountry: $currencyCountry
      identityId: $identityId
      includeSalesEventInfo: true
    ) {
      code
      codeStatus
      codeType
      consumptionMetadata {
        amountDisplay {
          amount
          currency
          placement
          symbol
        }
        minSalesPriceDisplay {
          amount
          currency
          placement
          symbol
        }
      }
      endDate
      namespace
      salesEvent(locale: $locale) {
        eventName
        eventSlug
        voucherImages {
          type
          url
        }
        voucherLink
      }
      startDate
    }
  }
}
"""

STORE_CONFIG_QUERY = """
query getStoreConfig(
  $includeCriticReviews: Boolean = false
  $locale: String!
  $sandboxId: String!
  $templateId: String
) {
  Product {
    sandbox(sandboxId: $sandboxId) {
      configuration(locale: $locale, templateId: $templateId) {
        ... on StoreConfiguration {
          configs {
            shortDescription
            criticReviews @include(if: $includeCriticReviews) {
              openCritic
            }
            socialLinks {
              platform
              url
            }
            supportedAudio
            supportedText
            tags(locale: $locale) {
              id
              name
              groupName
            }
            technicalRequirements {
              macos {
                minimum
                recommended
                title
              }
              windows {
                minimum
                recommended
                title
              }
            }
          }
        }
        ... on HomeConfiguration {
          configs {
            keyImages {
              ... on KeyImage {
                type
                url
                alt
              }
            }
            longDescription
          }
        }
      }
    }
  }
}
"""


def compress_query(query: str) -> str:
    return query.replace('  ', '').replace('\n', ' ')


game_query = compress_query(SEARCH_STORE_QUERY)
search_query = compress_query(SEARCH_STORE_QUERY)
wishlist_query = compress_query(WISHLIST_QUERY)
wishlist_add_query = compress_query(WISHLIST_ADD_QUERY)
wishlist_remove_query = compress_query(WISHLIST_REMOVE_QUERY)
coupons_query = compress_query(COUPONS_QUERY)
store_config_query = compress_query(STORE_CONFIG_QUERY)


if __name__ == '__main__':
    print(SEARCH_STORE_QUERY)
