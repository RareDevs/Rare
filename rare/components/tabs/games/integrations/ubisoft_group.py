import time
import webbrowser
from logging import getLogger
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, QThreadPool, QSize, pyqtSlot, Qt
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
    QPushButton,
    QGroupBox,
    QVBoxLayout,
)
from legendary.models.game import Game

from rare.lgndr.core import LegendaryCore
from rare.shared import RareCore
from rare.shared.workers.worker import Worker
from rare.utils.metrics import timelogger
from rare.utils.misc import icon
from rare.widgets.elide_label import ElideLabel
from rare.widgets.loading_widget import LoadingWidget

logger = getLogger("Ubisoft")


class UbiGetInfoWorker(Worker):
    class Signals(QObject):
        worker_finished = pyqtSignal(set, set, str)

    def __init__(self, core: LegendaryCore):
        super(UbiGetInfoWorker, self).__init__()
        self.signals = UbiGetInfoWorker.Signals()
        self.setAutoDelete(True)
        self.core = core

    def run_real(self) -> None:
        try:
            with timelogger(logger, "Request external auths"):
                external_auths = self.core.egs.get_external_auths()
            for ext_auth in external_auths:
                if ext_auth["type"] != "ubisoft":
                    continue
                ubi_account_id = ext_auth["externalAuthId"]
                break
            else:
                self.signals.worker_finished.emit(set(), set(), "")
                return

            with timelogger(logger, "Request uplay codes"):
                uplay_keys = self.core.egs.store_get_uplay_codes()
            key_list = uplay_keys["data"]["PartnerIntegration"]["accountUplayCodes"]
            redeemed = {k["gameId"] for k in key_list if k["redeemedOnUplay"]}

            if (entitlements := self.core.lgd.entitlements) is None:
                with timelogger(logger, "Request entitlements"):
                    entitlements = self.core.egs.get_user_entitlements()
                self.core.lgd.entitlements = entitlements
            entitlements = {i["entitlementName"] for i in entitlements}

            self.signals.worker_finished.emit(redeemed, entitlements, ubi_account_id)
        except Exception as e:
            logger.error(str(e))
            self.signals.worker_finished.emit(set(), set(), "error")


class UbiConnectWorker(Worker):
    class Signals(QObject):
        linked = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, ubi_account_id, partner_link_id):
        super(UbiConnectWorker, self).__init__()
        self.signals = UbiConnectWorker.Signals()
        self.core = core
        self.ubi_account_id = ubi_account_id
        self.partner_link_id = partner_link_id

    def run_real(self) -> None:
        if not self.ubi_account_id:  # debug
            time.sleep(2)
            self.signals.linked.emit("")
            return
        try:
            self.core.egs.store_claim_uplay_code(self.ubi_account_id, self.partner_link_id)
            self.core.egs.store_redeem_uplay_codes(self.ubi_account_id)
        except Exception as e:
            self.signals.linked.emit(str(e))
            return
        else:
            self.signals.linked.emit("")


class UbiLinkWidget(QFrame):
    def __init__(self, game: Game, ubi_account_id, activated: bool = False, parent=None):
        super(UbiLinkWidget, self).__init__(parent=parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.args = RareCore.instance().args()
        self.game = game
        self.ubi_account_id = ubi_account_id

        self.ok_indicator = QLabel(parent=self)
        self.ok_indicator.setPixmap(icon("fa.circle-o", color="grey").pixmap(20, 20))
        self.ok_indicator.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        self.title_label = ElideLabel(game.app_title, parent=self)

        self.link_button = QPushButton(self.tr("Redeem in Ubisoft"), parent=self)
        self.link_button.setMinimumWidth(150)
        self.link_button.clicked.connect(self.activate)

        if activated:
            self.link_button.setText(self.tr("Already activated"))
            self.link_button.setDisabled(True)
            self.ok_indicator.setPixmap(icon("fa.check-circle-o", color="green").pixmap(QSize(20, 20)))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(-1, 0, 0, 0)
        layout.addWidget(self.ok_indicator)
        layout.addWidget(self.title_label, stretch=1)
        layout.addWidget(self.link_button)

    def activate(self):
        self.link_button.setDisabled(True)
        # self.ok_indicator.setPixmap(icon("mdi.loading", color="grey").pixmap(20, 20))
        self.ok_indicator.setPixmap(icon("mdi.transit-connection-horizontal", color="grey").pixmap(20, 20))

        if self.args.debug:
            worker = UbiConnectWorker(RareCore.instance().core(), None, None)
        else:
            worker = UbiConnectWorker(
                RareCore.instance().core(), self.ubi_account_id, self.game.partner_link_id
            )
        worker.signals.linked.connect(self.worker_finished)
        QThreadPool.globalInstance().start(worker)

    def worker_finished(self, error):
        if not error:
            self.ok_indicator.setPixmap(icon("fa.check-circle-o", color="green").pixmap(QSize(20, 20)))
            self.link_button.setDisabled(True)
            self.link_button.setText(self.tr("Already activated"))
        else:
            self.ok_indicator.setPixmap(icon("fa.times-circle-o", color="red").pixmap(QSize(20, 20)))
            self.ok_indicator.setToolTip(error)
            self.link_button.setText(self.tr("Try again"))
            self.link_button.setDisabled(False)


class UbisoftGroup(QGroupBox):
    def __init__(self, parent=None):
        super(UbisoftGroup, self).__init__(parent=parent)
        self.setTitle(self.tr("Link Ubisoft Games"))
        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()
        self.args = RareCore.instance().args()

        self.thread_pool = QThreadPool.globalInstance()
        self.worker: Optional[UbiGetInfoWorker] = None

        self.info_label = QLabel(parent=self)
        self.info_label.setText(self.tr("Getting information about your redeemable Ubisoft games."))
        self.browser_button = QPushButton(self.tr("Link Ubisoft acccount"), parent=self)
        self.browser_button.setMinimumWidth(140)
        self.browser_button.clicked.connect(
            lambda: webbrowser.open("https://www.epicgames.com/id/link/ubisoft")
        )
        self.browser_button.setEnabled(False)

        self.loading_widget = LoadingWidget(self)
        self.loading_widget.stop()

        header_layout = QHBoxLayout()
        header_layout.addWidget(self.info_label, stretch=1)
        header_layout.addWidget(self.browser_button)

        layout = QVBoxLayout(self)
        layout.addLayout(header_layout)
        layout.addWidget(self.loading_widget)

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)

        if self.worker is not None:
            return

        for widget in self.findChildren(UbiLinkWidget, options=Qt.FindDirectChildrenOnly):
            widget.deleteLater()
        self.loading_widget.start()

        self.worker = UbiGetInfoWorker(self.core)
        self.worker.signals.worker_finished.connect(self.show_ubi_games)
        self.thread_pool.start(self.worker)
        super().showEvent(a0)

    @pyqtSlot(set, set, str)
    def show_ubi_games(self, redeemed: set, entitlements: set, ubi_account_id: str):
        self.worker = None
        if not redeemed and ubi_account_id != "error":
            logger.error(
                "No linked ubisoft account found! Link your accounts via your browser and try again."
            )
            self.info_label.setText(
                self.tr("Your account is not linked with Ubisoft. Please link your account and try again.")
            )
            self.browser_button.setEnabled(True)
        elif ubi_account_id == "error":
            self.info_label.setText(
                self.tr("An error has occurred while requesting your account's Ubisoft information.")
            )
            self.browser_button.setEnabled(True)
        else:
            self.browser_button.setEnabled(False)

            uplay_games = []
            activated = 0
            for rgame in self.rcore.ubisoft_games:
                game = rgame.game
                for dlc_data in game.metadata.get("dlcItemList", []):
                    if dlc_data["entitlementName"] not in entitlements:
                        continue
                    try:
                        app_name = dlc_data["releaseInfo"][0]["appId"]
                    except (IndexError, KeyError):
                        app_name = "unknown"

                    dlc_game = Game(app_name=app_name, app_title=dlc_data["title"], metadata=dlc_data)
                    if dlc_game.partner_link_type != "ubisoft":
                        continue
                    if dlc_game.partner_link_id in redeemed:
                        continue
                    uplay_games.append(dlc_game)

                if game.partner_link_type != "ubisoft":
                    continue
                if game.partner_link_id in redeemed:
                    activated += 1
                uplay_games.append(game)

            if not uplay_games:
                self.info_label.setText(self.tr("You don't own any Ubisoft games."))
            else:
                if activated == len(uplay_games):
                    self.info_label.setText(self.tr("All your Ubisoft games have already been activated."))
                else:
                    self.info_label.setText(
                        self.tr("You have <b>{}</b> games available to redeem.").format(
                            len(uplay_games) - activated
                        )
                    )
            logger.info(f"Found {len(uplay_games) - activated} game(s) to redeem.")

            self.loading_widget.stop()

            for game in uplay_games:
                widget = UbiLinkWidget(
                    game, ubi_account_id, activated=game.partner_link_id in redeemed, parent=self
                )
                self.layout().addWidget(widget)

            if self.args.debug:
                widget = UbiLinkWidget(
                    Game(app_name="RareTestGame", app_title="Super Fake Super Rare Super Test (Super?) Game"),
                    ubi_account_id,
                    activated=False,
                    parent=self,
                )
                self.layout().addWidget(widget)
                self.browser_button.setEnabled(True)
