class _ImageUrlModel:
    def __init__(self, front_tall: str = "", offer_image_tall: str = "",
                 thumbnail: str = "", front_wide: str = ""):
        self.front_tall = front_tall
        self.offer_image_tall = offer_image_tall
        self.thumbnail = thumbnail
        self.front_wide = front_wide

    @classmethod
    def from_json(cls, json_data: list):
        tmp = cls()
        for item in json_data:
            if item["type"] == "Thumbnail":
                tmp.thumbnail = item["url"]
            elif item["type"] == "DieselStoreFrontTall":
                tmp.front_tall = item["url"]
            elif item["type"] == "DieselStoreFrontWide":
                tmp.front_wide = item["url"]
            elif item["type"] == "OfferImageTall":
                tmp.offer_image_tall = item["url"]
        return tmp


class ShopGame:
    # TODO: Copyrights etc
    def __init__(self, title: str = "", image_urls: _ImageUrlModel = None, social_links: dict = None,
                 langs: list = None, reqs: dict = None, publisher: str = "", developer: str = "",
                 original_price: str = "", discount_price: str = ""):
        self.title = title
        self.image_urls = image_urls
        self.links = []
        if social_links:
            for item in social_links:
                if item.startswith("link"):
                    self.links.append(tuple((item.replace("link", ""), social_links[item])))
        else:
            self.links = []
        self.languages = langs
        self.reqs = reqs
        self.publisher = publisher
        self.developer = developer
        self.price = original_price
        self.discount_price = discount_price

    @classmethod
    def from_json(cls, api_data: dict, search_data: dict):
        if isinstance(api_data, list):
            for product in api_data:
                if product["_title"] == "home":
                    api_data = product
                    break

        tmp = cls()
        if "pages" in api_data.keys():
            api_data = api_data["pages"][0]
        tmp.title = api_data.get("productName", api_data.get("_title", "fail"))
        tmp.image_urls = _ImageUrlModel.from_json(search_data["keyImages"])
        links = api_data["data"]["socialLinks"]
        tmp.links = []
        for item in links:
            if item.startswith("link"):
                tmp.links.append(tuple((item.replace("link", ""), links[item])))
        tmp.available_voice_langs = api_data["data"]["requirements"].get("languages", "Failed")
        tmp.reqs = {}
        for i, system in enumerate(api_data["data"]["requirements"]["systems"]):
            tmp.reqs[system["systemType"]] = {}
            for req in system["details"]:
                try:
                    tmp.reqs[system["systemType"]][req["title"]] = (req["minimum"], req["recommended"])
                except KeyError:
                    pass
        tmp.publisher = api_data["data"]["meta"].get("publisher", "undefined")
        tmp.developer = api_data["data"]["meta"].get("developer", "undefined")
        tmp.price = search_data['price']['totalPrice']['fmtPrice']['originalPrice']
        tmp.discount_price = search_data['price']['totalPrice']['fmtPrice']['discountPrice']

        return tmp
