import time
import webbrowser
from logging import getLogger

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, QSize
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QSizePolicy, QPushButton
from qtawesome import icon

from legendary.models.game import Game
from rare import shared

logger = getLogger("Ubisoft")


class Signals(QObject):
    worker_finished = pyqtSignal(set, set, str)
    linked = pyqtSignal(str)


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
        if not self.ubi_account_id:  # debug
            time.sleep(2)
            self.signals.linked.emit("")
            return
        try:
            shared.core.egs.store_claim_uplay_code(self.ubi_account_id, self.partner_link_id)
            shared.core.egs.store_redeem_uplay_codes(self.ubi_account_id)
        except Exception as e:
            self.signals.linked.emit(str(e))
            return
        else:
            self.signals.linked.emit("")


class UbiLinkWidget(QWidget):
    def __init__(self, game: Game, ubi_account_id):
        super(UbiLinkWidget, self).__init__()
        self.setLayout(QHBoxLayout())
        self.game = game
        self.ubi_account_id = ubi_account_id

        self.title_label = QLabel(game.app_title)
        self.layout().addWidget(self.title_label)

        self.ok_indicator = QLabel()
        self.ok_indicator.setPixmap(icon("fa.info-circle", color="grey").pixmap(20, 20))
        self.ok_indicator.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.layout().addWidget(self.ok_indicator)

        self.link_button = QPushButton(self.tr("Redeem to Ubisoft") + ": Test" if shared.args.debug else "")
        self.layout().addWidget(self.link_button)
        self.link_button.clicked.connect(self.activate)

    def activate(self):
        self.link_button.setDisabled(True)
        # self.ok_indicator.setPixmap(icon("mdi.loading", color="grey").pixmap(20, 20))
        self.ok_indicator.setPixmap(icon("mdi.transit-connection-horizontal", color="grey").pixmap(20, 20))

        if shared.args.debug:
            worker = UbiConnectWorker(None, None)
        else:
            worker = UbiConnectWorker(self.ubi_account_id, self.game.partner_link_id)
        worker.signals.linked.connect(self.worker_finished)
        QThreadPool.globalInstance().start(worker)

    def worker_finished(self, error):
        if not error:
            self.ok_indicator.setPixmap(icon("ei.ok-circle", color="green").pixmap(QSize(20, 20)))
            self.link_button.setDisabled(True)
            self.link_button.setText(self.tr("Already activated"))
        else:
            self.ok_indicator.setPixmap(icon("fa.info-circle", color="red").pixmap(QSize(20, 20)))
            self.ok_indicator.setToolTip(error)
            self.link_button.setText(self.tr("Try again"))
            self.link_button.setDisabled(False)


class UbiActivationHelper(QObject):
    def __init__(self, widget: QWidget):
        super(UbiActivationHelper, self).__init__()
        self.widget = widget
        self.core = shared.core

        self.thread_pool = QThreadPool.globalInstance()
        worker = UbiGetInfoWorker()
        worker.signals.worker_finished.connect(self.show_ubi_games)
        self.thread_pool.start(worker)

    def show_ubi_games(self, redeemed: set, entitlements: set, ubi_account_id: str):
        if not redeemed and ubi_account_id != "error":
            logger.error('No linked ubisoft account found! Link your accounts via your browser and try again.')
            self.widget.layout().addWidget(
                QLabel(self.tr("Your account is not linked with Ubisoft. Please link your account first")))
            open_browser_button = QPushButton(self.tr("Open link page"))
            open_browser_button.clicked.connect(lambda: webbrowser.open("https://www.epicgames.com/id/link/ubisoft"))
            self.widget.layout().addWidget(open_browser_button)
            return
        elif ubi_account_id == "error":
            self.widget.layout().addWidget(QLabel(self.tr("An error occurred")))
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
                self.widget.layout().addWidget(
                    QLabel(self.tr("All your Ubisoft games have already been activated")))
            else:
                self.widget.layout().addWidget(QLabel(self.tr("You don't own any Ubisoft games")))
            if shared.args.debug:
                widget = UbiLinkWidget(Game(app_name="Test", app_title="This is a test game"), ubi_account_id)
                self.widget.layout().addWidget(widget)
            return
        logger.info(f'Found {len(uplay_games)} game(s) to redeem')

        for game in uplay_games:
            widget = UbiLinkWidget(game, ubi_account_id)
            self.widget.layout().addWidget(widget)
