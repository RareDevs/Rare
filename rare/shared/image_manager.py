import hashlib
import json
import pickle
import zlib
# from concurrent import futures
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from typing import Tuple, Dict, Union, Type, List, Callable

import requests
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    QObject,
    QSize,
    QThreadPool,
    QRunnable,
    QRect,
    QRectF,
)
from PyQt5.QtGui import (
    QPixmap,
    QImage,
    QPainter,
    QPainterPath,
    QBrush,
    QTransform,
    QPen,
)
from PyQt5.QtWidgets import QApplication
from legendary.models.game import Game

from rare.lgndr.core import LegendaryCore
from rare.models.image import ImageSize
from rare.models.signals import GlobalSignals
from rare.utils.paths import image_dir, resources_path, desktop_icon_suffix

# from requests_futures.sessions import FuturesSession

if TYPE_CHECKING:
    pass

logger = getLogger("ImageManager")


class ImageManager(QObject):
    class Worker(QRunnable):
        class Signals(QObject):
            # object: Game
            completed = pyqtSignal(object)

        def __init__(self, func: Callable, updates: List, json_data: Dict, game: Game):
            super(ImageManager.Worker, self).__init__()
            self.signals = ImageManager.Worker.Signals()
            self.setAutoDelete(True)
            self.func = func
            self.updates = updates
            self.json_data = json_data
            self.game = game

        def run(self):
            self.func(self.updates, self.json_data, self.game)
            logger.debug(f" Emitting singal for game {self.game.app_name} - {self.game.app_title}")
            self.signals.completed.emit(self.game)

    def __init__(self, signals: GlobalSignals, core: LegendaryCore):
        # lk: the ordering in __img_types matters for the order of fallbacks
        # self.__img_types: Tuple = ("DieselGameBoxTall", "Thumbnail", "DieselGameBoxLogo", "DieselGameBox", "OfferImageTall")
        self.__img_types: Tuple = ("DieselGameBoxTall", "Thumbnail", "DieselGameBoxLogo", "OfferImageTall")
        self.__dl_retries = 1
        self.__worker_app_names: List[str] = []
        super(QObject, self).__init__()
        self.signals = signals
        self.core = core

        self.image_dir: Path = image_dir()
        if not self.image_dir.is_dir():
            self.image_dir.mkdir()
            logger.info(f"Created image directory at {self.image_dir}")

        self.device = ImageSize.Preset(1, QApplication.instance().devicePixelRatio())

        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(8)

    def __img_dir(self, app_name: str) -> Path:
        return self.image_dir.joinpath(app_name)

    def __img_json(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath("image.json")

    def __img_cache(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath("image.cache")

    def __img_color(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath("installed.png")

    def __img_gray(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath("uninstalled.png")

    def __img_desktop_icon(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath(f"icon.{desktop_icon_suffix()}")

    def __prepare_download(self, game: Game, force: bool = False) -> Tuple[List, Dict]:
        if force and self.__img_dir(game.app_name).exists():
            self.__img_color(game.app_name).unlink(missing_ok=True)
            self.__img_gray(game.app_name).unlink(missing_ok=True)
            self.__img_desktop_icon(game.app_name).unlink(missing_ok=True)
        if not self.__img_dir(game.app_name).is_dir():
            self.__img_dir(game.app_name).mkdir()

        # Load image checksums
        if not self.__img_json(game.app_name).is_file():
            json_data: Dict = dict(zip(self.__img_types, [None] * len(self.__img_types)))
        else:
            json_data = json.load(open(self.__img_json(game.app_name), "r"))

        # lk: fast path for games without images, convert Rare's logo
        if not game.metadata.get("keyImages", False):
            if not self.__img_color(game.app_name).is_file() or not self.__img_gray(game.app_name).is_file():
                cache_data: Dict = dict(zip(self.__img_types, [None] * len(self.__img_types)))
                cache_data["DieselGameBoxTall"] = open(
                    resources_path.joinpath("images", "cover.png"), "rb"
                ).read()
                # cache_data["DieselGameBoxLogo"] = open(
                #         resources_path.joinpath("images", "Rare_nonsquared.png"), "rb").read()
                self.__convert(game, cache_data)
                json_data["cache"] = None
                json_data["scale"] = ImageSize.Image.pixel_ratio
                json_data["size"] = ImageSize.Image.size.__str__()
                json.dump(json_data, open(self.__img_json(game.app_name), "w"))

        # lk: Find updates or initialize if images are missing.
        # lk: `updates` will be empty for games without images
        # lk: so everything below it is skipped
        if not (
            self.__img_color(game.app_name).is_file()
            and self.__img_gray(game.app_name).is_file()
            and self.__img_desktop_icon(game.app_name).is_file()
        ):
            updates = [image for image in game.metadata["keyImages"] if image["type"] in self.__img_types]
        else:
            updates = []
            for image in game.metadata["keyImages"]:
                if image["type"] in self.__img_types:
                    if image["type"] not in json_data.keys() or json_data[image["type"]] != image["md5"]:
                        updates.append(image)

        return updates, json_data

    def __download(self, updates, json_data, game, use_async: bool = False) -> bool:
        # Decompress existing image.cache
        if not self.__img_cache(game.app_name).is_file():
            cache_data = dict(zip(self.__img_types, [None] * len(self.__img_types)))
        else:
            cache_data = self.__decompress(game)

        # lk: filter updates again against the cache now that it is available
        updates = [
            image
            for image in updates
            if cache_data.get(image["type"], None) is None or json_data[image["type"]] != image["md5"]
        ]

        # Download
        # # lk: Keep this here, so I don't have to go looking for it again,
        # # lk: it might be useful in the future.
        # if use_async and len(updates) > 1:
        #     session = FuturesSession(max_workers=len(self.__img_types))
        #     image_requests = []
        #     for image in updates:
        #         logger.info(f"Downloading {image['type']} for {game.app_title}")
        #         json_data[image["type"]] = image["md5"]
        #         payload = {"resize": 1, "w": ImageSize.Image.size.width(), "h": ImageSize.Image.size.height()}
        #         req = session.get(image["url"], params=payload)
        #         req.image_type = image["type"]
        #         image_requests.append(req)
        #     for req in futures.as_completed(image_requests):
        #         cache_data[req.image_type] = req.result().content
        # else:
        for image in updates:
            logger.info(f"Downloading {image['type']} for {game.app_title}")
            json_data[image["type"]] = image["md5"]
            payload = {"resize": 1, "w": ImageSize.Image.size.width(), "h": ImageSize.Image.size.height()}
            cache_data[image["type"]] = requests.get(image["url"], params=payload).content

        self.__convert(game, cache_data)
        # lk: don't keep the cache if there is no logo (kept for me)
        # if cache_data["DieselGameBoxLogo"] is not None:
        #     self.__compress(game, cache_data)
        self.__compress(game, cache_data)

        # hash image cache
        try:
            with open(self.__img_cache(game.app_name), "rb") as archive:
                archive_hash = hashlib.md5(archive.read()).hexdigest()
        except FileNotFoundError:
            archive_hash = None

        json_data["cache"] = archive_hash
        json_data["scale"] = ImageSize.Image.pixel_ratio
        json_data["size"] = {"w": ImageSize.Image.size.width(), "h": ImageSize.Image.size.height()}

        # write image.json
        with open(self.__img_json(game.app_name), "w") as file:
            json.dump(json_data, file)

        return bool(updates)

    __icon_overlay: Optional[QPainterPath] = None

    @staticmethod
    def __generate_icon_overlay(rect: QRect) -> QPainterPath:
        if ImageManager.__icon_overlay is not None:
            return ImageManager.__icon_overlay
        rounded_path = QPainterPath()
        margin = 0.1
        rounded_path.addRoundedRect(
            QRectF(
                rect.width() * margin,
                rect.height() * margin,
                rect.width() - (rect.width() * margin * 2),
                rect.height() - (rect.width() * margin * 2)
            ),
            rect.height() * 0.2,
            rect.height() * 0.2,
        )
        ImageManager.__icon_overlay = rounded_path
        return ImageManager.__icon_overlay

    @staticmethod
    def __convert_icon(cover: QImage) -> QImage:
        icon_size = QSize(128, 128)
        icon = QImage(icon_size, QImage.Format_ARGB32_Premultiplied)
        painter = QPainter(icon)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(icon.rect(), Qt.transparent)
        overlay = ImageManager.__generate_icon_overlay(icon.rect())
        brush = QBrush(cover)
        scale = max(icon.width()/cover.width(), icon.height()/cover.height())
        transform = QTransform().scale(scale, scale)
        brush.setTransform(transform)
        painter.fillPath(overlay, brush)
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        painter.drawPath(overlay)
        painter.end()
        return icon

    def __convert(self, game, images, force=False) -> None:
        for image in [self.__img_color(game.app_name), self.__img_gray(game.app_name)]:
            if force and image.exists():
                image.unlink(missing_ok=True)

        cover_data = None
        for image_type in self.__img_types:
            if images[image_type] is not None:
                cover_data = images[image_type]
                break

        cover = QImage()
        cover.loadFromData(cover_data)
        cover.convertToFormat(QImage.Format_ARGB32_Premultiplied)
        # lk: Images are not always 4/3, crop them to size
        factor = min(cover.width() // 3, cover.height() // 4)
        rem_w = (cover.width() - factor * 3) // 2
        rem_h = (cover.height() - factor * 4) // 2
        cover = cover.copy(rem_w, rem_h, factor * 3, factor * 4)

        if images["DieselGameBoxLogo"] is not None:
            logo = QImage()
            logo.loadFromData(images["DieselGameBoxLogo"])
            logo.convertToFormat(QImage.Format_ARGB32_Premultiplied)
            if logo.width() > cover.width():
                logo = logo.scaled(cover.width(), cover.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter = QPainter(cover)
            painter.drawImage((cover.width() - logo.width()) // 2, cover.height() - logo.height(), logo)
            painter.end()

        cover = cover.scaled(ImageSize.Image.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon = self.__convert_icon(cover)
        icon.save(str(self.__img_desktop_icon(game.app_name)), format=desktop_icon_suffix().upper())

        # this is not required if we ever want to re-apply the alpha channel
        # cover = cover.convertToFormat(QImage.Format_Indexed8)

        # add the alpha channel back to the cover
        cover = cover.convertToFormat(QImage.Format_ARGB32_Premultiplied)

        cover.save(str(self.__img_color(game.app_name)), format="PNG")
        # quick way to convert to grayscale
        cover = cover.convertToFormat(QImage.Format_Grayscale8)
        # add the alpha channel back to the grayscale cover
        cover = cover.convertToFormat(QImage.Format_ARGB32_Premultiplied)
        cover.save(str(self.__img_gray(game.app_name)), format="PNG")

    def __compress(self, game: Game, data: Dict) -> None:
        archive = open(self.__img_cache(game.app_name), "wb")
        cdata = zlib.compress(pickle.dumps(data), level=-1)
        archive.write(cdata)
        archive.close()

    def __decompress(self, game: Game) -> Dict:
        archive = open(self.__img_cache(game.app_name), "rb")
        try:
            data = zlib.decompress(archive.read())
            data = pickle.loads(data)
        except zlib.error:
            data = dict(zip(self.__img_types, [None] * len(self.__img_types)))
        finally:
            archive.close()
        return data

    def download_image(
        self, game: Game, load_callback: Callable[[], None], priority: int, force: bool = False
    ) -> None:
        updates, json_data = self.__prepare_download(game, force)
        if not updates:
            load_callback()
            return
        if updates and game.app_name not in self.__worker_app_names:
            image_worker = ImageManager.Worker(self.__download, updates, json_data, game)
            self.__worker_app_names.append(game.app_name)

            image_worker.signals.completed.connect(load_callback)
            image_worker.signals.completed.connect(lambda g: self.__worker_app_names.remove(g.app_name))
            self.threadpool.start(image_worker, priority)

    def download_image_blocking(self, game: Game, force: bool = False) -> None:
        updates, json_data = self.__prepare_download(game, force)
        if not updates:
            return
        if updates:
            self.__download(updates, json_data, game, use_async=True)

    def __get_cover(
        self, container: Union[Type[QPixmap], Type[QImage]], app_name: str, color: bool = True
    ) -> Union[QPixmap, QImage]:
        ret = container()
        if not app_name:
            raise RuntimeError("app_name is an empty string")
        if color:
            if self.__img_color(app_name).is_file():
                ret.load(str(self.__img_color(app_name)))
        else:
            if self.__img_gray(app_name).is_file():
                ret.load(str(self.__img_gray(app_name)))
        if not ret.isNull():
            ret.setDevicePixelRatio(ImageSize.Image.pixel_ratio)
            # lk: Scaling happens at painting. It might be inefficient so leave this here as an alternative
            # lk: If this is uncommented, the transformation in ImageWidget should be adjusted also
            ret = ret.scaled(self.device.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            ret.setDevicePixelRatio(self.device.pixel_ratio)
        return ret

    def get_pixmap(self, app_name: str, color: bool = True) -> QPixmap:
        """
        Use when the image is to be presented directly on the screen.

        @param app_name: The RareGame object for this game
        @param color: True to load the colored pixmap, False to load the grayscale
        @return: QPixmap
        """
        pixmap: QPixmap = self.__get_cover(QPixmap, app_name, color)
        return pixmap

    def get_image(self, app_name: str, color: bool = True) -> QImage:
        """
        Use when the image has to be manipulated before being rendered.

        @param app_name: The RareGame object for this game
        @param color: True to load the colored image, False to load the grayscale
        @return: QImage
        """
        image: QImage = self.__get_cover(QImage, app_name, color)
        return image
