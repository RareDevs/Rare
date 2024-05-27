import hashlib
import json
import pickle
import zlib

# from concurrent import futures
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Set
from typing import Tuple, Dict, Union, Type, List, Callable

import requests
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QSize, QThreadPool, QRunnable, QRect, QRectF, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPainterPath, QBrush, QTransform, QPen
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
            logger.debug(f"Emitting singal for {self.game.app_name} ({self.game.app_title})")
            self.signals.completed.emit(self.game)

    def __init__(self, signals: GlobalSignals, core: LegendaryCore):
        # lk: the ordering in __img_types matters for the order of fallbacks
        # {'AndroidIcon', 'DieselGameBox', 'DieselGameBoxLogo', 'DieselGameBoxTall', 'DieselGameBoxWide',
        #  'ESRB', 'Featured', 'OfferImageTall', 'OfferImageWide', 'Screenshot', 'Thumbnail'}
        self.__img_tall_types: Tuple = ("DieselGameBoxTall", "OfferImageTall", "Thumbnail")
        self.__img_wide_types: Tuple = ("DieselGameBoxWide", "DieselGameBox", "OfferImageWide", "Screenshot")
        self.__img_logo_types: Tuple = ("DieselGameBoxLogo",)
        self.__img_types: Tuple = self.__img_tall_types + self.__img_wide_types + self.__img_logo_types
        self.__dl_retries = 1
        self.__worker_app_names: Set[str] = set()
        super(QObject, self).__init__()
        self.signals = signals
        self.core = core

        self.image_dir: Path = image_dir()
        if not self.image_dir.is_dir():
            self.image_dir.mkdir()
            logger.info(f"Created image directory at {self.image_dir}")

        self.device = ImageSize.Preset(1, QApplication.instance().devicePixelRatio())

        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(6)

    def __img_dir(self, app_name: str) -> Path:
        return self.image_dir.joinpath(app_name)

    def __img_json(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath("image.json")

    def __img_cache(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath("image.cache")

    def __img_tall_color(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath("tall.png")

    def __img_tall_gray(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath("tall_uninstalled.png")

    def __img_wide_color(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath("wide.png")

    def __img_wide_gray(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath("wide_uninstalled.png")

    def __img_logo(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath("logo.png")

    def __img_icon(self, app_name: str) -> Path:
        return self.__img_dir(app_name).joinpath(f"icon.{desktop_icon_suffix()}")

    def __img_all(self, app_name: str) -> Tuple:
        return (
            self.__img_icon(app_name),
            self.__img_tall_color(app_name),
            self.__img_tall_gray(app_name),
            self.__img_wide_color(app_name),
            self.__img_tall_gray(app_name),
        )

    def __prepare_download(self, game: Game, force: bool = False) -> Tuple[List, Dict]:
        if force and self.__img_dir(game.app_name).exists():
            for file in self.__img_all(game.app_name):
                file.unlink(missing_ok=True)
        if not self.__img_dir(game.app_name).is_dir():
            self.__img_dir(game.app_name).mkdir()

        # Load image checksums
        if not self.__img_json(game.app_name).is_file():
            json_data: Dict = dict(zip(self.__img_types, [None] * len(self.__img_types)))
        else:
            json_data = json.load(open(self.__img_json(game.app_name), "r"))

        # Only download the best matching candidate for each image category
        def best_match(key_images: List, image_types: Tuple) -> Dict:
            matches = sorted(
                filter(lambda image: image["type"] in image_types, key_images),
                key=lambda x: image_types.index(x["type"]) if x["type"] in image_types else len(image_types),
                reverse=False,
            )
            try:
                best = matches[0]
            except IndexError as e:
                best = {}
            return best

        candidates = tuple(
            image
            for image in [
                best_match(game.metadata.get("keyImages", []), self.__img_tall_types),
                best_match(game.metadata.get("keyImages", []), self.__img_wide_types),
                best_match(game.metadata.get("keyImages", []), self.__img_logo_types),
            ]
            if bool(image)
        )

        # lk: Find updates or initialize if images are missing.
        # lk: `updates` will be empty for games without images
        # lk: so everything below it is skipped
        updates = []
        if not all(file.is_file() for file in self.__img_all(game.app_name)):
            # lk: fast path for games without images, convert Rare's logo
            if not candidates:
                cache_data: Dict = dict(zip(self.__img_types, [None] * len(self.__img_types)))
                with open(resources_path.joinpath("images", "cover.png"), "rb") as fd:
                    cache_data["DieselGameBoxTall"] = fd.read()
                    fd.seek(0)
                    cache_data["DieselGameBoxWide"] = fd.read()
                # cache_data["DieselGameBoxLogo"] = open(
                #         resources_path.joinpath("images", "Rare_nonsquared.png"), "rb").read()
                self.__convert(game, cache_data)
                json_data["cache"] = None
                json_data["scale"] = ImageSize.Image.pixel_ratio
                json_data["size"] = {"w": ImageSize.Image.size.width(), "h": ImageSize.Image.size.height()}
                json.dump(json_data, open(self.__img_json(game.app_name), "w"))
            else:
                updates = [image for image in candidates if image["type"] in self.__img_types]
        else:
            for image in candidates:
                if image["type"] in self.__img_types:
                    if image["type"] not in json_data.keys() or json_data[image["type"]] != image["md5"]:
                        updates.append(image)

        return updates, json_data

    def __download(self, updates: List, json_data: Dict, game: Game, use_async: bool = False) -> bool:
        # Decompress existing image.cache
        if not self.__img_cache(game.app_name).is_file():
            cache_data = dict(zip(self.__img_types, [None] * len(self.__img_types)))
        else:
            cache_data = self.__decompress(game)

        # lk: filter updates again against the cache now that it is available
        # images in cache don't need to be downloaded again.
        downloads = [
            image
            for image in updates
            if (cache_data.get(image["type"], None) is None or json_data[image["type"]] != image["md5"])
        ]

        # Download
        # # lk: Keep this here, so I don't have to go looking for it again,
        # # lk: it might be useful in the future.
        # if use_async:
        #     session = FuturesSession(max_workers=len(self.__img_types))
        #     image_requests = []
        #     for image in downloads:
        #         logger.info(f"Downloading {image['type']} for {game.app_title}")
        #         json_data[image["type"]] = image["md5"]
        #         if image["type"] in self.__img_tall_types:
        #             payload = {"resize": 1, "w": ImageSize.Image.size.width(), "h": ImageSize.Image.size.height()}
        #         elif image["type"] in self.__img_wide_types:
        #             payload = {"resize": 1, "w": ImageSize.ImageWide.size.width(), "h": ImageSize.ImageWide.size.height()}
        #         else:
        #             # Set the larger of the sizes for everything else
        #             payload = {"resize": 1, "w": ImageSize.ImageWide.size.width(), "h": ImageSize.ImageWide.size.height()}
        #         req = session.get(image["url"], params=payload)
        #         req.image_type = image["type"]
        #         image_requests.append(req)
        #     for req in futures.as_completed(image_requests):
        #         cache_data[req.image_type] = req.result().content
        # else:
        for image in downloads:
            logger.info(f"Downloading {image['type']} for {game.app_name} ({game.app_title})")
            json_data[image["type"]] = image["md5"]
            if image["type"] in self.__img_tall_types:
                payload = {"resize": 1, "w": ImageSize.Image.size.width(), "h": ImageSize.Image.size.height()}
            elif image["type"] in self.__img_wide_types:
                payload = {"resize": 1, "w": ImageSize.ImageWide.size.width(), "h": ImageSize.ImageWide.size.height()}
            else:
                # Set the larger of the sizes for everything else
                payload = {"resize": 1, "w": ImageSize.ImageWide.size.width(), "h": ImageSize.ImageWide.size.height()}
            try:
                # cache_data[image["type"]] = requests.get(image["url"], params=payload).content
                cache_data[image["type"]] = requests.get(image["url"], params=payload, timeout=10).content
            except Exception as e:
                logger.error(e)
                return False

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
        margin = 0.05
        rounded_path.addRoundedRect(
            QRectF(
                rect.width() * margin,
                rect.height() * margin,
                rect.width() - (rect.width() * margin * 2),
                rect.height() - (rect.width() * margin * 2),
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
        scale = max(icon.width() / cover.width(), icon.height() / cover.height())
        transform = QTransform().scale(scale, scale)
        brush.setTransform(transform)
        painter.fillPath(overlay, brush)
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        painter.drawPath(overlay)
        painter.end()
        return icon

    def __convert(self, game, images, force=False) -> None:
        for file in self.__img_all(game.app_name):
            if force and file.exists():
                file.unlink(missing_ok=True)

        def find_image_data(image_types: Tuple):
            data = None
            for image_type in image_types:
                if images.get(image_type, None) is not None:
                    data = images[image_type]
                    break
            return data

        tall_data = find_image_data(self.__img_tall_types)
        wide_data = find_image_data(self.__img_wide_types)
        logo_data = find_image_data(self.__img_logo_types)

        def convert_image(image_data, logo_data, preset: ImageSize.Preset) -> QImage:
            image = QImage()
            image.loadFromData(image_data)
            image.convertToFormat(QImage.Format_ARGB32_Premultiplied)
            # lk: Images are not always at the correct aspect ratio, so crop them to size
            wr, hr = preset.aspect_ratio
            factor = min(image.width() // wr, image.height() // hr)
            rem_w = (image.width() - factor * wr) // 2
            rem_h = (image.height() - factor * hr) // 2
            image = image.copy(rem_w, rem_h, factor * wr, factor * hr)

            if logo_data is not None:
                logo = QImage()
                logo.loadFromData(logo_data)
                logo.convertToFormat(QImage.Format_ARGB32_Premultiplied)
                if logo.width() > image.width():
                    logo = logo.scaled(image.width(), image.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter = QPainter(image)
                painter.drawImage((image.width() - logo.width()) // 2, image.height() - logo.height(), logo)
                painter.end()

            return image.scaled(preset.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        tall = convert_image(tall_data, logo_data, ImageSize.Image)
        wide = convert_image(wide_data, logo_data, ImageSize.ImageWide)

        icon = self.__convert_icon(tall)
        icon.save(str(self.__img_icon(game.app_name)), format=desktop_icon_suffix().upper())

        def save_image(image: QImage, color_path: Path, gray_path: Path):
            # this is not required if we ever want to re-apply the alpha channel
            # image = image.convertToFormat(QImage.Format_Indexed8)
            # add the alpha channel back to the cover
            image = image.convertToFormat(QImage.Format_ARGB32_Premultiplied)
            image.save(color_path.as_posix(), format="PNG")
            # quick way to convert to grayscale
            image = image.convertToFormat(QImage.Format_Grayscale8)
            # add the alpha channel back to the grayscale cover
            image = image.convertToFormat(QImage.Format_ARGB32_Premultiplied)
            image.save(gray_path.as_posix(), format="PNG")

        save_image(tall, self.__img_tall_color(game.app_name), self.__img_tall_gray(game.app_name))
        save_image(wide, self.__img_wide_color(game.app_name), self.__img_wide_gray(game.app_name))

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

    def __append_to_queue(self, game: Game):
        self.__worker_app_names.add(game.app_name)

    @pyqtSlot(object)
    def __remove_from_queue(self, game: Game):
        self.__worker_app_names.remove(game.app_name)

    def download_image(
            self, game: Game, load_callback: Callable[[], None], priority: int, force: bool = False
    ) -> None:
        if game.app_name in self.__worker_app_names:
            return
        self.__append_to_queue(game)
        updates, json_data = self.__prepare_download(game, force)
        if not updates:
            self.__remove_from_queue(game)
            load_callback()
        else:
            # Copy the data because we are going to be a thread and we modify them later on
            image_worker = ImageManager.Worker(self.__download, updates.copy(), json_data.copy(), game)
            image_worker.signals.completed.connect(self.__remove_from_queue)
            image_worker.signals.completed.connect(load_callback)
            self.threadpool.start(image_worker, priority)

    def download_image_launch(
            self, game: Game, callback: Callable[[], None], priority: int, force: bool = False
    ) -> None:
        if self.__img_cache(game.app_name).is_file() and not force:
            return
        self.download_image(game, callback, priority, force)

    def download_image_blocking(self, game: Game, force: bool = False) -> None:
        updates, json_data = self.__prepare_download(game, force)
        if not updates:
            return
        if updates:
            self.__download(updates, json_data, game, use_async=True)

    def __get_cover(
        self, container: Union[Type[QPixmap], Type[QImage]], app_name: str, color: bool
    ) -> Union[QPixmap, QImage]:
        ret = container()
        if not app_name:
            raise RuntimeError("app_name is an empty string")
        if color:
            if self.__img_tall_color(app_name).is_file():
                ret.load(self.__img_tall_color(app_name).as_posix())
        else:
            if self.__img_tall_gray(app_name).is_file():
                ret.load(self.__img_tall_gray(app_name).as_posix())
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
