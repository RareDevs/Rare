
FEED_QUERY = '''
query feedQuery(
  $locale: String!
  $countryCode: String
  $offset: Int
  $postsPerPage: Int
  $category: String
) {
  TransientStream {
    myTransientFeed(countryCode: $countryCode, locale: $locale) {
      id
      activity {
        ... on LinkAccountActivity {
          type
          created_at
          platforms
        }
        ... on SuggestedFriendsActivity {
          type
          created_at
          platform
          suggestions {
            epicId
            epicDisplayName
            platformFullName
            platformAvatar
          }
        }
        ... on IncomingInvitesActivity {
          type
          created_at
          invites {
            epicId
            epicDisplayName
          }
        }
        ... on RecentPlayersActivity {
          type
          created_at
          players {
            epicId
            epicDisplayName
            playedGameName
          }
        }
      }
    }
  }
  Blog {
    dieselBlogPosts: getPosts(
      locale: $locale
      offset: $offset
      postsPerPage: $postsPerPage
      category: $category
    ) {
      blogList {
        _id
        author
        category
        content
        urlPattern
        slug
        sticky
        title
        date
        image
        shareImage
        trendingImage
        url
        featured
        link
        externalLink
      }
    }
  }
}
'''

REVIEWS_QUERY = '''
query productReviewsQuery($sku: String!) {
  OpenCritic {
    productReviews(sku: $sku) {
      id
      name
      openCriticScore
      reviewCount
      percentRecommended
      openCriticUrl
      award
      topReviews {
        publishedDate
        externalUrl
        snippet
        language
        score
        author
        ScoreFormat {
          id
          description
        }
        OutletId
        outletName
        displayScore
      }
    }
  }
}
'''

MEDIA_QUERY = '''
query fetchMediaRef($mediaRefId: String!) {
  Media {
    getMediaRef(mediaRefId: $mediaRefId) {
      accountId
      outputs {
        duration
        url
        width
        height
        key
        contentType
      }
      namespace
    }
  }
}
'''

ADDONS_QUERY = '''
query getAddonsByNamespace(
  $categories: String!
  $count: Int!
  $country: String!
  $locale: String!
  $namespace: String!
  $sortBy: String!
  $sortDir: String!
) {
  Catalog {
    catalogOffers(
      namespace: $namespace
      locale: $locale
      params: {
        category: $categories
        count: $count
        country: $country
        sortBy: $sortBy
        sortDir: $sortDir
      }
    ) {
      elements {
        countriesBlacklist
        customAttributes {
          key
          value
        }
        description
        developer
        effectiveDate
        id
        isFeatured
        keyImages {
          type
          url
        }
        lastModifiedDate
        longDescription
        namespace
        offerType
        productSlug
        releaseDate
        status
        technicalDetails
        title
        urlSlug
      }
    }
  }
}
'''

CATALOG_QUERY = '''
query catalogQuery(
  $category: String
  $count: Int
  $country: String!
  $keywords: String
  $locale: String
  $namespace: String!
  $sortBy: String
  $sortDir: String
  $start: Int
  $tag: String
) {
  Catalog {
    catalogOffers(
      namespace: $namespace
      locale: $locale
      params: {
        count: $count
        country: $country
        category: $category
        keywords: $keywords
        sortBy: $sortBy
        sortDir: $sortDir
        start: $start
        tag: $tag
      }
    ) {
      elements {
        isFeatured
        collectionOfferIds
        title
        id
        namespace
        description
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
          }
          lineOffers {
            appliedRules {
              id
              endDate
            }
          }
        }
        linkedOfferId
        linkedOffer {
          effectiveDate
          customAttributes {
            key
            value
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
'''

CATALOG_TAGS_QUERY = '''
query catalogTags($namespace: String!) {
  Catalog {
    tags(namespace: $namespace, start: 0, count: 999) {
      elements {
        aliases
        id
        name
        referenceCount
        status
      }
    }
  }
}
'''

PREREQUISITES_QUERY = '''
query fetchPrerequisites($offerParams: [OfferParams]) {
  Launcher {
    prerequisites(offerParams: $offerParams) {
      namespace
      offerId
      missingPrerequisiteItems
      satisfiesPrerequisites
    }
  }
}
'''

PROMOTIONS_QUERY = '''
query promotionsQuery(
  $namespace: String!
  $country: String!
  $locale: String!
) {
  Catalog {
    catalogOffers(
      namespace: $namespace
      locale: $locale
      params: {
        category: "freegames"
        country: $country
        sortBy: "effectiveDate"
        sortDir: "asc"
      }
    ) {
      elements {
        title
        description
        id
        namespace
        categories {
          path
        }
        linkedOfferNs
        linkedOfferId
        keyImages {
          type
          url
        }
        productSlug
        promotions {
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
    }
  }
}
'''

OFFERS_QUERY = '''
query catalogQuery(
  $productNamespace: String!
  $offerId: String!
  $locale: String
  $country: String!
  $includeSubItems: Boolean!
) {
  Catalog {
    catalogOffer(namespace: $productNamespace, id: $offerId, locale: $locale) {
      title
      id
      namespace
      description
      effectiveDate
      expiryDate
      isCodeRedemptionOnly
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
      price(country: $country) {
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
    }
    offerSubItems(namespace: $productNamespace, id: $offerId)
      @include(if: $includeSubItems) {
      namespace
      id
      releaseInfo {
        appId
        platform
      }
    }
  }
}
'''

SEARCH_STORE_QUERY = '''
query searchStoreQuery(
  $allowCountries: String
  $category: String
  $count: Int
  $country: String!
  $keywords: String
  $locale: String
  $namespace: String
  $itemNs: String
  $sortBy: String
  $sortDir: String
  $start: Int
  $tag: String
  $releaseDate: String
  $withPrice: Boolean = false
  $withPromotions: Boolean = false
) {
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
'''