import os


class InstallOptionsModel:
    def __init__(self, app_name: str, base_path: str = os.path.expanduser("~/legendary"),
                 max_workers: int = os.cpu_count() * 2, repair: bool = False, no_install: bool = False,
                 ignore_space_req: bool = False, force: bool = False, sdl_list: list = ['']
                 ):
        self.app_name = app_name
        self.base_path = base_path
        self.max_workers = max_workers
        self.repair = repair
        self.no_install = no_install
        self.ignore_space_req = ignore_space_req
        self.force = force
        self.sdl_list = sdl_list


class InstallDownloadModel:
    def __init__(self, dlmanager, analysis, game, igame, repair: bool, repair_file: str):
        self.dlmanager = dlmanager
        self.analysis = analysis
        self.game = game
        self.igame = igame
        self.repair = repair
        self.repair_file = repair_file


class InstallQueueItemModel:
    def __init__(self, status_q=None, download: InstallDownloadModel = None, options: InstallOptionsModel = None):
        self.status_q = status_q
        self.download = download
        self.options = options

    def __bool__(self):
        return (self.status_q is not None) and (self.download is not None) and (self.options is not None)


class ShopGame:
    # TODO: Copyrights etc
    def __init__(self, title: str = "", image_urls: dict = None, social_links: dict = None,
                 langs: list = None, reqs: list = None, publisher: str = "", developer: str = "",
                 price: str = ""):
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
        self.reqs = reqs  # {"Betriebssystem":win7, processor:i9 9900k, ram...}; Note: name from language
        self.publisher = publisher
        self.developer = developer
        self.price = price

    @classmethod
    def from_json(cls, api_data: dict, search_data: dict):
        print(api_data)
        if isinstance(api_data, list):
            for product in api_data:
                if product["_title"] == "home":
                    api_data = product
                    print("home")
                    break

        tmp = cls()
        tmp.title = api_data.get("productName", "undefined")
        """tmp.img_urls = {
            "DieselImage": data["pages"][0]["data"]["about"]["image"]["src"],
            "banner": data["pages"][0]["data"]["hero"]["backgroundImageUrl"]
        }"""
        links = api_data["pages"][0]["data"]["socialLinks"]
        tmp.links = []
        for item in links:
            if item.startswith("link"):
                tmp.links.append(tuple((item.replace("link", ""), links[item])))
        tmp.available_voice_langs = api_data["pages"][0]["data"]["requirements"]["languages"]
        tmp.reqs = []
        for i, system in enumerate(api_data["pages"][0]["data"]["requirements"]["systems"]):
            tmp.reqs.append({"name": system["systemType"], "value": []})
            for req in system["details"]:
                tmp.reqs[i]["value"].append(tuple((req["minimum"], req["recommended"])))

        tmp.publisher = api_data["pages"][0]["data"]["meta"].get("publisher", "undefined")
        tmp.developer = api_data["pages"][0]["data"]["meta"].get("developer", "undefined")
        tmp.price = {
            "normal": search_data["price"]["totalPrice"]["originalPrice"]
        }
        if price := search_data["price"]["totalPrice"].get("discountPrice"):
            tmp.price["discount"] = price

        return tmp
