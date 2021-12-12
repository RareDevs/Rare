import re
import webbrowser
from logging import getLogger
from typing import Tuple

from PyQt5.QtCore import QThreadPool, QRunnable, QObject, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSizePolicy, QWidget, QFileDialog, QMessageBox, QLabel, QPushButton, QHBoxLayout
from qtawesome import icon

import rare.shared as shared
from legendary.models.game import Game
from rare.ui.components.tabs.settings.legendary import Ui_LegendarySettings
from rare.utils.extra_widgets import PathEdit, IndicatorLineEdit
from rare.utils.utils import get_size

logger = getLogger("LegendarySettings")


class Signals(QObject):
    worker_finished = pyqtSignal(set, set, str)
    connected = pyqtSignal(str)

class UbiGetInfoWorker(QRunnable):
    def __init__(self):
        super(UbiGetInfoWorker, self).__init__()
        self.signals = Signals()
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            external_auths = shared.core.egs.get_external_auths()
            for ext_auth in external_auths:
                if ext_auth['type'] != 'ubisoft':
                    continue
                ubi_account_id = ext_auth['externalAuthId']
                break
            else:
                self.signals.worker_finished.emit(set(), set(), "")
                return

            uplay_keys = shared.core.egs.store_get_uplay_codes()
            key_list = uplay_keys['data']['PartnerIntegration']['accountUplayCodes']
            redeemed = {k['gameId'] for k in key_list if k['redeemedOnUplay']}

            entitlements = shared.core.egs.get_user_entitlements()
            entitlements = {i['entitlementName'] for i in entitlements}
            self.signals.worker_finished.emit(redeemed, entitlements, ubi_account_id)
        except Exception as e:
            logger.error(str(e))
            self.signals.worker_finished.emit(set(), set(), "error")

class UbiConnectWorker(QRunnable):
    def __init__(self, ubi_account_id, partner_link_id):
        super(UbiConnectWorker, self).__init__()
        self.signals = Signals()
        self.setAutoDelete(True)
        self.ubi_account_id = ubi_account_id
        self.partner_link_id = partner_link_id

    def run(self) -> None:
        try:
            shared.core.egs.store_claim_uplay_code(self.ubi_account_id, self.partner_link_id)
            shared.core.egs.store_redeem_uplay_codes(self.ubi_account_id)
        except Exception as e:
            self.signals.connected.emit(str(e))
            return
        else:
            self.signals.connected.emit("")


class UbiLinkWidget(QWidget):
    def __init__(self, game: Game, ubi_account_id):
        super(UbiLinkWidget, self).__init__()
        self.setLayout(QHBoxLayout())
        self.game = game
        self.ubi_account_id = ubi_account_id

        self.ok_indicator = QLabel()
        self.ok_indicator.setVisible(False)
        self.ok_indicator.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.layout().addWidget(self.ok_indicator)

        self.title_label = QLabel(game.app_title)
        self.layout().addWidget(self.title_label)
        if not shared.args.debug:
            self.link_button = QPushButton(self.tr("Redeem to Ubisoft"))
            self.layout().addWidget(self.link_button)
            self.link_button.clicked.connect(self.activate)
        else:
            btn = QPushButton(self.tr("Test: error"))
            self.layout().addWidget(btn)
            btn.clicked.connect(lambda: self.worker_finished("Any Error"))

            ok_button = QPushButton(self.tr("Test: Ok"))
            self.layout().addWidget(ok_button)
            ok_button.clicked.connect(lambda: self.worker_finished(""))

    def activate(self):
        if shared.args.debug:
            self.worker_finished("Connection Error")
            return
        worker = UbiConnectWorker(self.ubi_account_id, self.game.partner_link_id)
        worker.signals.worker_finished.connect(self.worker_finished)
        QThreadPool.globalInstance().start(worker)

    def worker_finished(self, error):
        self.ok_indicator.setVisible(True)
        if not error:
            self.ok_indicator.setPixmap(icon("ei.ok-circle", color="green").pixmap(QSize(20, 20)))
        else:
            self.ok_indicator.setPixmap(icon("fa.info-circle", color="red").pixmap(QSize(20, 20)))
            self.ok_indicator.setToolTip(error)


class LegendarySettings(QWidget, Ui_LegendarySettings):
    def __init__(self, parent=None):
        super(LegendarySettings, self).__init__(parent=parent)
        self.setupUi(self)

        self.core = shared.core

        # Default installation directory
        self.install_dir = PathEdit(self.core.get_default_install_dir(),
                                    file_type=QFileDialog.DirectoryOnly,
                                    save_func=self.path_save)
        self.install_dir_layout.addWidget(self.install_dir)

        # Max Workers
        max_workers = self.core.lgd.config['Legendary'].getint('max_workers', fallback=0)
        self.max_worker_spin.setValue(max_workers)
        self.max_worker_spin.valueChanged.connect(self.max_worker_save)
        # Max memory
        max_memory = self.core.lgd.config['Legendary'].getint('max_memory', fallback=0)
        self.max_memory_spin.setValue(max_memory)
        self.max_memory_spin.valueChanged.connect(self.max_memory_save)
        # Preferred CDN
        preferred_cdn = self.core.lgd.config['Legendary'].get('preferred_cdn', fallback="")
        self.preferred_cdn_line.setText(preferred_cdn)
        self.preferred_cdn_line.textChanged.connect(self.preferred_cdn_save)
        # Disable HTTPS
        disable_https = self.core.lgd.config['Legendary'].getboolean('disable_https', fallback=False)
        self.disable_https_check.setChecked(disable_https)
        self.disable_https_check.stateChanged.connect(self.disable_https_save)

        # Cleanup
        self.clean_button.clicked.connect(
            lambda: self.cleanup(False)
        )
        self.clean_keep_manifests_button.clicked.connect(
            lambda: self.cleanup(True)
        )

        self.locale_edit = IndicatorLineEdit(
            f"{self.core.language_code}-{self.core.country_code}",
            edit_func=self.locale_edit_cb,
            save_func=self.locale_save_cb,
            horiz_policy=QSizePolicy.Minimum,
            parent=self
        )
        self.locale_layout.addWidget(self.locale_edit)

        self.thread_pool = QThreadPool.globalInstance()
        worker = UbiGetInfoWorker()
        worker.signals.worker_finished.connect(self.show_ubi_games)
        self.thread_pool.start(worker)

    def show_ubi_games(self, redeemed: set, entitlements: set, ubi_account_id: str):
        if not redeemed and ubi_account_id != "error":
            logger.error('No linked ubisoft account found! Link your accounts via your browser and try again.')
            self.ubisoft_gb.layout().addWidget(
                QLabel(self.tr("Your account is not linked with Ubisoft. Please link your account first")))
            open_browser_button = QPushButton(self.tr("Open link page"))
            open_browser_button.clicked.connect(lambda: webbrowser.open("https://www.epicgames.com/id/link/ubisoft"))
            self.ubisoft_gb.layout().addWidget(open_browser_button)
            return
        elif ubi_account_id == "error":
            self.ubisoft_gb.layout().addWidget(QLabel(self.tr("An error occurred")))
            return

        games = self.core.get_game_list(False)
        uplay_games = []
        activated = 0
        for game in games:
            for dlc_data in game.metadata.get('dlcItemList', []):
                if dlc_data['entitlementName'] not in entitlements:
                    continue

                try:
                    app_name = dlc_data['releaseInfo'][0]['appId']
                except (IndexError, KeyError):
                    app_name = 'unknown'

                dlc_game = Game(app_name=app_name, app_title=dlc_data['title'], metadata=dlc_data)
                if dlc_game.partner_link_type != 'ubisoft':
                    continue
                if dlc_game.partner_link_id in redeemed:
                    continue
                uplay_games.append(dlc_game)

            if game.partner_link_type != "ubisoft":
                continue
            if game.partner_link_id in redeemed:
                activated += 1
                continue
            uplay_games.append(game)

        if not uplay_games:
            if activated >= 1:
                self.ubisoft_gb.layout().addWidget(QLabel(self.tr("All your Ubisoft games have already been activated")))
            else:
                self.ubisoft_gb.layout().addWidget(QLabel(self.tr("You don't own any Ubisoft games")))
            if shared.args.debug:
                widget = UbiLinkWidget(Game(app_name="Test", app_title="Test Game"), ubi_account_id)
                self.ubisoft_gb.layout().addWidget(widget)
            return
        logger.info(f'Found {len(uplay_games)} game(s) to redeem')

        for game in uplay_games:
            widget = UbiLinkWidget(game, ubi_account_id)
            self.ubisoft_gb.layout().addWidget(widget)


    @staticmethod
    def locale_edit_cb(text: str) -> Tuple[bool, str]:
        if text:
            if re.match("^[a-zA-Z]{2,3}[-_][a-zA-Z]{2,3}$", text):
                language, country = text.replace("_", "-").split("-")
                text = "-".join([language.lower(), country.upper()])
            return bool(re.match("^[a-z]{2,3}-[A-Z]{2,3}$", text)), text
        else:
            return True, text

    def locale_save_cb(self, text: str):
        if text:
            self.core.egs.language_code, self.core.egs.country_code = text.split("-")
            self.core.lgd.config.set("Legendary", "locale", text)
        else:
            if self.core.lgd.config.has_option("Legendary", "locale"):
                self.core.lgd.config.remove_option("Legendary", "locale")
        self.core.lgd.save_config()

    def path_save(self, text: str):
        self.core.lgd.config["Legendary"]["install_dir"] = text
        if not text and "install_dir" in self.core.lgd.config["Legendary"].keys():
            self.core.lgd.config["Legendary"].pop("install_dir")
        else:
            logger.debug("Set config install_dir to " + text)
        self.core.lgd.save_config()

    def max_worker_save(self, workers: str):
        if workers := int(workers):
            self.core.lgd.config.set("Legendary", "max_workers", str(workers))
        else:
            self.core.lgd.config.remove_option("Legendary", "max_workers")
        self.core.lgd.save_config()

    def max_memory_save(self, memory: str):
        if memory := int(memory):
            self.core.lgd.config.set("Legendary", "max_memory", str(memory))
        else:
            self.core.lgd.config.remove_option("Legendary", "max_memory")
        self.core.lgd.save_config()

    def preferred_cdn_save(self, cdn: str):
        if cdn:
            self.core.lgd.config.set("Legendary", "preferred_cdn", cdn.strip())
        else:
            self.core.lgd.config.remove_option("Legendary", "preferred_cdn")
        self.core.lgd.save_config()

    def disable_https_save(self, checked: int):
        self.core.lgd.config.set("Legendary", "disable_https", str(bool(checked)).lower())
        self.core.lgd.save_config()

    def cleanup(self, keep_manifests):
        before = self.core.lgd.get_dir_size()
        logger.debug('Removing app metadata...')
        app_names = set(g.app_name for g in self.core.get_assets(update_assets=False))
        self.core.lgd.clean_metadata(app_names)

        if not keep_manifests:
            logger.debug('Removing manifests...')
            installed = [(ig.app_name, ig.version) for ig in self.core.get_installed_list()]
            installed.extend((ig.app_name, ig.version) for ig in self.core.get_installed_dlc_list())
            self.core.lgd.clean_manifests(installed)

        logger.debug('Removing tmp data')
        self.core.lgd.clean_tmp_data()

        after = self.core.lgd.get_dir_size()
        logger.info(f'Cleanup complete! Removed {(before - after) / 1024 / 1024:.02f} MiB.')
        if (before - after) > 0:
            QMessageBox.information(self, "Cleanup", self.tr("Cleanup complete! Successfully removed {}").format(
                get_size(before - after)))
        else:
            QMessageBox.information(self, "Cleanup", "Nothing to clean")
