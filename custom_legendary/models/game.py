# coding: utf-8

from enum import Enum


class GameAsset:
    def __init__(self):
        self.app_name = ''
        self.asset_id = ''
        self.build_version = ''
        self.catalog_item_id = ''
        self.label_name = ''
        self.namespace = ''
        self.metadata = dict()

    @classmethod
    def from_egs_json(cls, json):
        tmp = cls()
        tmp.app_name = json.get('appName', '')
        tmp.asset_id = json.get('assetId', '')
        tmp.build_version = json.get('buildVersion', '')
        tmp.catalog_item_id = json.get('catalogItemId', '')
        tmp.label_name = json.get('labelName', '')
        tmp.namespace = json.get('namespace', '')
        tmp.metadata = json.get('metadata', {})
        return tmp

    @classmethod
    def from_json(cls, json):
        tmp = cls()
        tmp.app_name = json.get('app_name', '')
        tmp.asset_id = json.get('asset_id', '')
        tmp.build_version = json.get('build_version', '')
        tmp.catalog_item_id = json.get('catalog_item_id', '')
        tmp.label_name = json.get('label_name', '')
        tmp.namespace = json.get('namespace', '')
        tmp.metadata = json.get('metadata', {})
        return tmp


class Game:
    def __init__(self, app_name='', app_title='', asset_info=None, app_version='', metadata=None):
        self.metadata = dict() if metadata is None else metadata  # store metadata from EGS
        self.asset_info = asset_info if asset_info else GameAsset()  # asset info from EGS

        self.app_version = app_version
        self.app_name = app_name
        self.app_title = app_title
        self.base_urls = []  # base urls for download, only really used when cached manifest is current

    @property
    def is_dlc(self):
        return self.metadata and 'mainGameItem' in self.metadata

    @property
    def supports_cloud_saves(self):
        return self.metadata and (self.metadata.get('customAttributes', {}).get('CloudSaveFolder') is not None)

    @classmethod
    def from_json(cls, json):
        tmp = cls()
        tmp.metadata = json.get('metadata', dict())
        tmp.asset_info = GameAsset.from_json(json.get('asset_info', dict()))
        tmp.app_name = json.get('app_name', 'undefined')
        tmp.app_title = json.get('app_title', 'undefined')
        tmp.app_version = json.get('app_version', 'undefined')
        tmp.base_urls = json.get('base_urls', list())
        return tmp

    @property
    def __dict__(self):
        """This is just here so asset_info gets turned into a dict as well"""
        return dict(metadata=self.metadata, asset_info=self.asset_info.__dict__,
                    app_name=self.app_name, app_title=self.app_title,
                    app_version=self.app_version, base_urls=self.base_urls)


class InstalledGame:
    def __init__(self, app_name='', title='', version='', manifest_path='', base_urls=None,
                 install_path='', executable='', launch_parameters='', prereq_info=None,
                 can_run_offline=False, requires_ot=False, is_dlc=False, save_path=None,
                 needs_verification=False, install_size=0, egl_guid='', install_tags=None):
        self.app_name = app_name
        self.title = title
        self.version = version

        self.manifest_path = manifest_path
        self.base_urls = list() if not base_urls else base_urls
        self.install_path = install_path
        self.executable = executable
        self.launch_parameters = launch_parameters
        self.prereq_info = prereq_info
        self.can_run_offline = can_run_offline
        self.requires_ot = requires_ot
        self.is_dlc = is_dlc
        self.save_path = save_path
        self.needs_verification = needs_verification
        self.install_size = install_size
        self.egl_guid = egl_guid
        self.install_tags = install_tags if install_tags else []

    @classmethod
    def from_json(cls, json):
        tmp = cls()
        tmp.app_name = json.get('app_name', '')
        tmp.version = json.get('version', '')
        tmp.title = json.get('title', '')

        tmp.manifest_path = json.get('manifest_path', '')
        tmp.base_urls = json.get('base_urls', list())
        tmp.install_path = json.get('install_path', '')
        tmp.executable = json.get('executable', '')
        tmp.launch_parameters = json.get('launch_parameters', '')
        tmp.prereq_info = json.get('prereq_info', None)

        tmp.can_run_offline = json.get('can_run_offline', False)
        tmp.requires_ot = json.get('requires_ot', False)
        tmp.is_dlc = json.get('is_dlc', False)
        tmp.save_path = json.get('save_path', None)
        tmp.needs_verification = json.get('needs_verification', False) is True
        tmp.install_size = json.get('install_size', 0)
        tmp.egl_guid = json.get('egl_guid', '')
        tmp.install_tags = json.get('install_tags', [])
        return tmp


class SaveGameFile:
    def __init__(self, app_name='', filename='', manifest='', datetime=None):
        self.app_name = app_name
        self.filename = filename
        self.manifest_name = manifest
        self.datetime = datetime


class SaveGameStatus(Enum):
    LOCAL_NEWER = 0
    REMOTE_NEWER = 1
    SAME_AGE = 2
    NO_SAVE = 3


class VerifyResult(Enum):
    HASH_MATCH = 0
    HASH_MISMATCH = 1
    FILE_MISSING = 2
    OTHER_ERROR = 3


x = {'title': 'Frostpunk',
     'id': 'b43c1e1e0ca14b6784b323c59c751136', 'namespace': 'd5241c76f178492ea1540fce45616757',
     'description': 'Frostpunk', 'effectiveDate': '2099-01-01T00:00:00.000Z', 'offerType': 'OTHERS', 'expiryDate': None,
     'status': 'ACTIVE', 'isCodeRedemptionOnly': True, 'keyImages': [{'type': 'VaultClosed',
                                                                      'url': 'https://cdn1.epicgames.com/d5241c76f178492ea1540fce45616757/offer/EpicVault_Clean_OPEN_V10_LightsON-1920x1080-75e6d0636a6083944570a1c6f94ead4f.png'},
                                                                     {'type': 'DieselStoreFrontWide',
                                                                      'url': 'https://cdn1.epicgames.com/salesEvent/salesEvent/EGS_Frostpunk_wide_2560x1440-ef2f4d458120af0839dde35b1a022828'},
                                                                     {'type': 'DieselStoreFrontTall',
                                                                      'url': 'https://cdn1.epicgames.com/salesEvent/salesEvent/EGS_Frostpunk_Tall_1200x1600-c71dc27cfe505c6c662c49011b36a0c5'}],
     'seller': {'id': 'o-ufmrk5furrrxgsp5tdngefzt5rxdcn', 'name': 'Epic Dev Test Account'}, 'productSlug': 'frostpunk',
     'urlSlug': 'free-games-06', 'url': None,
     'items': [{'id': '8341d7c7e4534db7848cc428aa4cbe5a', 'namespace': 'd5241c76f178492ea1540fce45616757'}],
     'customAttributes': [{'key': 'com.epicgames.app.freegames.vault.close', 'value': '[]'},
                          {'key': 'com.epicgames.app.blacklist', 'value': '[]'},
                          {'key': 'com.epicgames.app.freegames.vault.slug',
                           'value': 'news/the-epic-mega-sale-returns-for-2021'},
                          {'key': 'publisherName', 'value': '11 bit studios'}, {'key': 'dupe', 'value': '[]'},
                          {'key': 'com.epicgames.app.freegames.vault.open', 'value': '[]'},
                          {'key': 'developerName', 'value': '11 bit studios'},
                          {'key': 'com.epicgames.app.productSlug', 'value': 'frostpunk'}],
     'categories': [{'path': 'freegames/vaulted'}, {'path': 'freegames'}, {'path': 'games'}, {'path': 'applications'}],
     'tags': [], 'price': {'totalPrice': {'discountPrice': 0, 'originalPrice': 0, 'voucherDiscount': 0, 'discount': 0,
                                          'currencyCode': 'USD', 'currencyInfo': {'decimals': 2},
                                          'fmtPrice': {'originalPrice': '0', 'discountPrice': '0',
                                                       'intermediatePrice': '0'}},
                           'lineOffers': [{'appliedRules': []}]}, 'promotions': {'promotionalOffers': [],
                                                                                 'upcomingPromotionalOffers': [{
                                                                                                                   'promotionalOffers': [
                                                                                                                       {
                                                                                                                           'startDate': '2021-06-03T15:00:00.000Z',
                                                                                                                           'endDate': '2021-06-10T15:00:00.000Z',
                                                                                                                           'discountSetting': {
                                                                                                                               'discountType': 'PERCENTAGE',
                                                                                                                               'discountPercentage': 0}}]}]}}
