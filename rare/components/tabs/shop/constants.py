from PyQt5.QtCore import QObject


# Class to use QObject.tr()
class Constants(QObject):
    def __init__(self):
        super(Constants, self).__init__()
        self.categories = sorted([
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
            (self.tr("Sport"), "1283")
        ], key=lambda x: x[0])

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
            (self.tr("Apps"), "software/edition/base")
        ]


game_query = "query searchStoreQuery($allowCountries: String, $category: String, $count: Int, $country: String!, " \
             "$keywords: String, $locale: String, $namespace: String, $withMapping: Boolean = false, $itemNs: String, " \
             "$sortBy: String, $sortDir: String, $start: Int, $tag: String, $releaseDate: String, $withPrice: Boolean " \
             "= false, $withPromotions: Boolean = false, $priceRange: String, $freeGame: Boolean, $onSale: Boolean, " \
             "$effectiveDate: String) {\n  Catalog {\n    searchStore(\n      allowCountries: $allowCountries\n      " \
             "category: $category\n      count: $count\n      country: $country\n      keywords: $keywords\n      " \
             "locale: $locale\n      namespace: $namespace\n      itemNs: $itemNs\n      sortBy: $sortBy\n      " \
             "sortDir: $sortDir\n      releaseDate: $releaseDate\n      start: $start\n      tag: $tag\n      " \
             "priceRange: $priceRange\n      freeGame: $freeGame\n      onSale: $onSale\n      effectiveDate: " \
             "$effectiveDate\n    ) {\n      elements {\n        title\n        id\n        namespace\n        " \
             "description\n        effectiveDate\n        keyImages {\n          type\n          url\n        }\n     " \
             "   currentPrice\n        seller {\n          id\n          name\n        }\n        productSlug\n       " \
             " urlSlug\n        url\n        tags {\n          id\n        }\n        items {\n          id\n         " \
             " namespace\n        }\n        customAttributes {\n          key\n          value\n        }\n        " \
             "categories {\n          path\n        }\n        catalogNs @include(if: $withMapping) {\n          " \
             "mappings(pageType: \"productHome\") {\n            pageSlug\n            pageType\n          }\n        " \
             "}\n        offerMappings @include(if: $withMapping) {\n          pageSlug\n          pageType\n        " \
             "}\n        price(country: $country) @include(if: $withPrice) {\n          totalPrice {\n            " \
             "discountPrice\n            originalPrice\n            voucherDiscount\n            discount\n           " \
             " currencyCode\n            currencyInfo {\n              decimals\n            }\n            fmtPrice(" \
             "locale: $locale) {\n              originalPrice\n              discountPrice\n              " \
             "intermediatePrice\n            }\n          }\n          lineOffers {\n            appliedRules {\n     " \
             "         id\n              endDate\n              discountSetting {\n                discountType\n     " \
             "         }\n            }\n          }\n        }\n        promotions(category: $category) @include(if: " \
             "$withPromotions) {\n          promotionalOffers {\n            promotionalOffers {\n              " \
             "startDate\n              endDate\n              discountSetting {\n                discountType\n       " \
             "         discountPercentage\n              }\n            }\n          }\n          " \
             "upcomingPromotionalOffers {\n            promotionalOffers {\n              startDate\n              " \
             "endDate\n              discountSetting {\n                discountType\n                " \
             "discountPercentage\n              }\n            }\n          }\n        }\n      }\n      paging {\n   " \
             "     count\n        total\n      }\n    }\n  }\n}\n "
