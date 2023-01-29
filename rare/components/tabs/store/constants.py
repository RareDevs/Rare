from PyQt5.QtCore import QObject


# Class to use QObject.tr()
class Constants(QObject):
    def __init__(self):
        super(Constants, self).__init__()
        self.categories = sorted(
            [
                (self.tr("Action"), "1216"),
                (self.tr("Adventure"), "1117"),
                (self.tr("Puzzle"), "1298"),
                (self.tr("Open world"), "1307"),
                (self.tr("Racing"), "1212"),
                (self.tr("RPG"), "1367"),
                (self.tr("Shooter"), "1210"),
                (self.tr("Strategy"), "1115"),
                (self.tr("Survival"), "1080"),
                (self.tr("First Person"), "1294"),
                (self.tr("Indie"), "1263"),
                (self.tr("Simulation"), "1393"),
                (self.tr("Sport"), "1283"),
            ],
            key=lambda x: x[0],
        )

        self.platforms = [
            ("MacOS", "9548"),
            ("Windows", "9547"),
        ]
        self.others = [
            (self.tr("Single player"), "1370"),
            (self.tr("Multiplayer"), "1203"),
            (self.tr("Controller"), "9549"),
            (self.tr("Co-op"), "1264"),
        ]

        self.types = [
            (self.tr("Editor"), "editors"),
            (self.tr("Game"), "games/edition/base"),
            (self.tr("Bundle"), "bundles/games"),
            (self.tr("Add-on"), "addons"),
            (self.tr("Apps"), "software/edition/base"),
        ]


game_query = """
query searchStoreQuery($allowCountries: String, $category: String, $count: Int, $country: String!, $keywords: String, $locale: String, $namespace: String, $withMapping: Boolean = false, $itemNs: String, $sortBy: String, $sortDir: String, $start: Int, $tag: String, $releaseDate: String, $withPrice: Boolean = false, $withPromotions: Boolean = false, $priceRange: String, $freeGame: Boolean, $onSale: Boolean, $effectiveDate: String) {
  Catalog {
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
    ) {
      elements {
        title
        id
        namespace
        description
        effectiveDate
        keyImages {
          type
          url
        }
        currentPrice
        seller {
          id
          name
        }
        productSlug
        urlSlug
        url
        tags {
          id
        }
        items {
          id
          namespace
        }
        customAttributes {
          key
          value
        }
        categories {
          path
        }
        catalogNs @include(if: $withMapping) {
          mappings(pageType: "productHome") {
            pageSlug
            pageType
          }
        }
        offerMappings @include(if: $withMapping) {
          pageSlug
          pageType
        }
        price(country: $country) @include(if: $withPrice) {
          totalPrice {
            discountPrice
            originalPrice
            voucherDiscount
            discount
            currencyCode
            currencyInfo {
              decimals
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
        }
        promotions(category: $category) @include(if: $withPromotions) {
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
        }
      }
      paging {
        count
        total
      }
    }
  }
}
"""

search_query = """
query searchStoreQuery($allowCountries: String, $category: String, $count: Int, $country: String!, $keywords: String, $locale: String, $namespace: String, $itemNs: String, $sortBy: String, $sortDir: String, $start: Int, $tag: String, $releaseDate: String, $withPrice: Boolean = false, $withPromotions: Boolean = false, $priceRange: String, $freeGame: Boolean, $onSale: Boolean, $effectiveDate: String) {
  Catalog {
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
    ) {
      elements {
        title
        id
        namespace
        description
        effectiveDate
        keyImages {
          type
          url
        }
        currentPrice
        seller {
          id
          name
        }
        productSlug
        urlSlug
        url
        tags {
          id
        }
        items {
          id
          namespace
        }
        customAttributes {
          key
          value
        }
        categories {
          path
        }
        catalogNs {
          mappings(pageType: "productHome") {
            pageSlug
            pageType
          }
        }
        offerMappings {
          pageSlug
          pageType
        }
        price(country: $country) @include(if: $withPrice) {
          totalPrice {
            discountPrice
            originalPrice
            voucherDiscount
            discount
            currencyCode
            currencyInfo {
              decimals
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
        }
        promotions(category: $category) @include(if: $withPromotions) {
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
        }
      }
      paging {
        count
        total
      }
    }
  }
}
"""

wishlist_query = """
query wishlistQuery($country:String!, $locale:String) {
  Wishlist {
    wishlistItems {
      elements {
        id
        order
        created
        offerId
        updated
        namespace
        offer(locale: $locale) {
          productSlug
          urlSlug
          title
          id
          namespace
          offerType
          expiryDate
          status
          isCodeRedemptionOnly
          description
          effectiveDate
          keyImages {
            type
            url
          }
          seller {
            id
            name
          }
          productSlug
          urlSlug
          items {
            id
            namespace
          }
          customAttributes {
            key
            value
          }
          catalogNs {
            mappings(pageType: "productHome") {
              pageSlug
              pageType
            }
          }
          offerMappings {
            pageSlug
            pageType
          }
          categories {
            path
          }
          price(country: $country) {
            totalPrice {
              discountPrice
              originalPrice
              voucherDiscount
              discount
              fmtPrice(locale: $locale) {
                originalPrice
                discountPrice
                intermediatePrice
              }
              currencyCode
              currencyInfo {
                decimals
                symbol
              }
            }
            lineOffers {
              appliedRules {
                id
                endDate
              }
            }
          }
        }
      }
    }
  }
}
"""

add_to_wishlist_query = """
mutation addWishlistMutation($namespace: String!, $offerId: String!, $country:String!, $locale:String) {
    Wishlist {
        addToWishlist(namespace: $namespace, offerId: $offerId) {
            wishlistItem {
                id,
                order,
                created,
                offerId,
                updated,
                namespace,
                isFirstTime
                offer {
                    productSlug
                    urlSlug
                    title
                    id
                    namespace
                    offerType
                    expiryDate
                    status
                    isCodeRedemptionOnly
                    description
                    effectiveDate
                    keyImages {
                        type
                        url
                    }
                    seller {
                        id
                        name
                    }
                    productSlug
                    urlSlug
                    items {
                        id
                        namespace
                    }
                    customAttributes {
                        key
                        value
                    }
                    catalogNs {
                        mappings(pageType: "productHome") {
                            pageSlug
                            pageType
                        }
                    }
                    offerMappings {
                        pageSlug
                        pageType
                    }
                    categories {
                        path
                    }
                    price(country: $country) {
                        totalPrice {
                            discountPrice
                            originalPrice
                            voucherDiscount
                            discount
                            fmtPrice(locale: $locale) {
                                originalPrice
                                discountPrice
                                intermediatePrice
                            }
                            currencyCode
                            currencyInfo {
                                decimals
                                symbol
                            }
                        }
                        lineOffers {
                            appliedRules {
                                id
                                endDate
                            }
                        }
                    }
                }

            }
            success
        }
    }
}
"""

remove_from_wishlist_query = """
mutation removeFromWishlistMutation($namespace: String!, $offerId: String!, $operation: RemoveOperation!) {
    Wishlist {
        removeFromWishlist(namespace: $namespace, offerId: $offerId, operation: $operation) {
            success
        }
    }
}
"""

coupon_query = """
query getCoupons($currencyCountry: String!, $identityId: String!, $locale: String) {
    CodeRedemption {
        coupons(currencyCountry: $currencyCountry, identityId: $identityId, includeSalesEventInfo: true) {
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


# if __name__ == "__main__":
#     from sgqlc import introspection, codegen
#
#     coupon = codegen.operation.parse_graphql(coupon_query)
#     codegen.schema.
#     print(coupon.)
