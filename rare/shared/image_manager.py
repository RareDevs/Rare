import hashlib
import json
import pickle
import threading
import zlib
from logging import getLogger
from multiprocessing import cpu_count
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

import requests
from legendary.lfs.eos import EOSOverlayApp
from legendary.models.game import Game
from PySide6.QtCore import (
    QObject,
    QRect,
    QRectF,
    QRunnable,
    QSize,
    Qt,
    QThreadPool,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QBrush,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QTransform,
)

from rare.lgndr.core import LegendaryCore
from rare.models.image import ImageSize, ImageType
from rare.models.signals import GlobalSignals
from rare.utils.paths import (
    desktop_icon_path,
    desktop_icon_suffix,
    image_dir,
    image_dir_game,
    image_icon_path,
    image_tall_path,
    image_wide_path,
    resources_path,
)

if TYPE_CHECKING:
    pass


class ImageWorkerSignals(QObject):
    # object: Game
    completed = Signal(object)


class ImageWorker(QRunnable):
    def __init__(self, func: Callable[[Game, bool], None], game: Game, force: bool):
        super(ImageWorker, self).__init__()
        self.signals = ImageWorkerSignals()
        self.setAutoDelete(True)
        self.func: Callable[[Game, bool], None] = func
        self.game: Game = game
        self.force: bool = force

    def run(self):
        self.func(self.game, self.force)
        self.signals.completed.emit(self.game)
        self.signals.disconnect(self.signals)
        self.signals.deleteLater()


class ImageManager(QObject):
    def __init__(self, signals: GlobalSignals, core: LegendaryCore):
        self.logger = getLogger(type(self).__name__)
        self._cache_version = 2
        # lk: the ordering in _img_types matters for the order of fallbacks
        # {'AndroidIcon', 'DieselGameBox', 'DieselGameBoxLogo', 'DieselGameBoxTall', 'DieselGameBoxWide',
        #  'ESRB', 'Featured', 'OfferImageTall', 'OfferImageWide', 'Screenshot', 'Thumbnail'}
        self._img_tall_types: Tuple = (
            "DieselGameBoxTall",
            "OfferImageTall",
            "Thumbnail",
        )
        self._img_wide_types: Tuple = (
            "DieselGameBoxWide",
            "DieselGameBox",
            "OfferImageWide",
            "Screenshot",
        )
        self._img_logo_types: Tuple = ("DieselGameBoxLogo",)
        self._img_types: Tuple = self._img_tall_types + self._img_wide_types + self._img_logo_types
        self._dl_retries = 1
        self._worker_lock = threading.Lock()
        self._worker_app_names: Set[str] = set()
        super(ImageManager, self).__init__()
        self.signals = signals
        self.core = core

        self.image_dir: Path = image_dir()
        if not self.image_dir.is_dir():
            self.image_dir.mkdir()
            self.logger.info("Created image directory at %s", self.image_dir)

        self.threadpool = QThreadPool(self)
        self.threadpool.setMaxThreadCount(min(cpu_count() * 2, 16))

    @staticmethod
    def _img_json(app_name: str) -> Path:
        return image_dir_game(app_name).joinpath("image.json")

    @staticmethod
    def _img_cache(app_name: str) -> Path:
        return image_dir_game(app_name).joinpath("image.cache")

    @staticmethod
    def _img_all(app_name: str) -> Tuple:
        return (
            image_tall_path(app_name),
            image_tall_path(app_name, color=False),
            image_wide_path(app_name),
            image_wide_path(app_name, color=False),
            image_icon_path(app_name),
            image_icon_path(app_name, color=False),
            desktop_icon_path(app_name),
        )

    def has_pixmaps(self, app_name: str) -> bool:
        return all(file.is_file() for file in self._img_all(app_name))

    def _prepare_download(self, game: Game, force: bool = False) -> Tuple[List, Dict]:
        if force and image_dir_game(game.app_name).exists():
            for file in self._img_all(game.app_name):
                file.unlink(missing_ok=True)
        if not image_dir_game(game.app_name).is_dir():
            image_dir_game(game.app_name).mkdir()

        # Load image checksums
        if not self._img_json(game.app_name).is_file():
            json_data: Dict = dict(zip(self._img_types, [None] * len(self._img_types)))
            json_data["version"] = self._cache_version
        else:
            json_data = json.load(open(self._img_json(game.app_name), "r"))

        # Only download the best matching candidate for each image category
        def best_match(key_images: List, image_types: Tuple) -> Dict:
            matches = sorted(
                filter(lambda image: image["type"] in image_types, key_images),
                key=lambda x: image_types.index(x["type"]) if x["type"] in image_types else len(image_types),
                reverse=False,
            )
            try:
                best = matches[0]
            except IndexError:
                best = {}
            return best

        candidates = tuple(
            image
            for image in [
                best_match(game.metadata.get("keyImages", []), self._img_tall_types),
                best_match(game.metadata.get("keyImages", []), self._img_wide_types),
                best_match(game.metadata.get("keyImages", []), self._img_logo_types),
            ]
            if bool(image)
        )

        # lk: Find updates or initialize if images are missing.
        # lk: `updates` will be empty for games without images
        # lk: so everything below it is skipped
        # TODO: Move this into the thread, maybe, concurrency could help here too
        updates = []
        if (not self.has_pixmaps(game.app_name)):
            if not candidates:
                cover = "epic.png" if game.app_name == EOSOverlayApp.app_name else "cover.png"
                # lk: fast path for games without images, convert Rare's logo
                cache_data: Dict = dict(zip(self._img_types, [None] * len(self._img_types)))
                with open(resources_path.joinpath("images", cover), "rb") as fd:
                    cache_data["DieselGameBoxTall"] = fd.read()
                with open(resources_path.joinpath("images", cover), "rb") as fd:
                    cache_data["DieselGameBoxWide"] = fd.read()
                # cache_data["DieselGameBoxLogo"] = open(
                #         resources_path.joinpath("images", "logo.png"), "rb").read()
                self._convert(game, cache_data)
                json_data["cache"] = None
                json_data["scale"] = ImageSize.Tall.pixel_ratio
                json_data["size"] = {
                    "w": ImageSize.Tall.size.width(),
                    "h": ImageSize.Tall.size.height(),
                }
                with open(self._img_json(game.app_name), "w", encoding="utf-8") as file:
                    json.dump(json_data, file)
            else:
                updates = [image for image in candidates if image["type"] in self._img_types]
        else:
            for image in candidates:
                if image["type"] in self._img_types:
                    if image["type"] not in json_data.keys() or json_data[image["type"]] != image["md5"]:
                        updates.append(image)

        return updates, json_data

    def _download(self, updates: List, json_data: Dict, game: Game) -> bool:
        # Decompress existing image.cache
        if not self._img_cache(game.app_name).is_file():
            cache_data: Dict[str, Any] = dict(zip(self._img_types, [None] * len(self._img_types)))
        else:
            cache_data = self._decompress(game)

        # lk: filter updates again against the cache now that it is available
        # images in cache don't need to be downloaded again.
        downloads = [
            image
            for image in updates
            if (cache_data.get(image["type"], None) is None or json_data[image["type"]] != image["md5"])
        ]

        for image in downloads:
            self.logger.debug(
                "Downloading %s for %s (%s)",
                image["type"],
                game.app_name,
                game.app_title,
            )
            json_data[image["type"]] = image["md5"]
            if image["type"] in self._img_tall_types:
                payload = {
                    "resize": 1,
                    "w": ImageSize.Tall.size.width(),
                    "h": ImageSize.Tall.size.height(),
                }
            elif image["type"] in self._img_wide_types:
                payload = {
                    "resize": 1,
                    "w": ImageSize.Wide.size.width(),
                    "h": ImageSize.Wide.size.height(),
                }
            else:
                # Set the larger of the sizes for everything else
                payload = {
                    "resize": 1,
                    "w": ImageSize.Wide.size.width(),
                    "h": ImageSize.Wide.size.height(),
                }
            try:
                cache_data[image["type"]] = requests.get(image["url"], params=payload, timeout=10).content
            except Exception as e:
                self.logger.error(e)
                return False

        # lk: test the cached and downloaded data if they describe an image with valid dimensions
        # I do not like this, it should add a bunch of processing for something simple but I am out of ideas
        for image in updates:
            image_data = QImage().fromData(cache_data[image["type"]])
            if not (image_data.width() and image_data.height()):
                with open(resources_path.joinpath("images", "cover.png"), "rb") as fd:
                    cache_data[image["type"]] = fd.read()
                json_data[image["type"]] = None
                self.logger.error(
                    "Invalid image %s data for %s (%s)",
                    image["type"],
                    game.app_name,
                    game.app_title,
                )
            del image_data

        self._convert(game, cache_data)
        # lk: don't keep the cache if there is no logo (kept for me)
        # if cache_data["DieselGameBoxLogo"] is not None:
        #     self._compress(game, cache_data)
        self._compress(game, cache_data)

        # hash image cache
        try:
            with open(self._img_cache(game.app_name), "rb") as archive:
                archive_hash = hashlib.md5(archive.read()).hexdigest()
        except FileNotFoundError:
            archive_hash = None

        json_data["cache"] = archive_hash
        json_data["scale"] = ImageSize.Tall.pixel_ratio
        json_data["size"] = {
            "w": ImageSize.Tall.size.width(),
            "h": ImageSize.Tall.size.height(),
        }

        # write image.json
        with open(self._img_json(game.app_name), "w", encoding="utf-8") as file:
            json.dump(json_data, file)

        return bool(updates)

    _icon_overlay: Optional[QPainterPath] = None

    def _generate_icon_overlay(self, rect: QRect) -> QPainterPath:
        if self._icon_overlay is not None:
            return self._icon_overlay
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
        self._icon_overlay = rounded_path
        return self._icon_overlay

    def _convert_image(self, image_data, logo_data, preset: ImageSize.Preset) -> QImage:
        image = QImage()
        image.loadFromData(image_data)
        image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        if image.height() > image.width() and preset.orientation == ImageType.Wide:
            image = image.transformed(QTransform().rotate(90.0))
        if image.height() < image.width() and preset.orientation == ImageType.Tall:
            image = image.transformed(QTransform().rotate(-90.0))
        # lk: Images are not always at the correct aspect ratio, so crop them to size
        wr, hr = preset.aspect_ratio
        factor = min(image.width() // wr, image.height() // hr)
        rem_w = (image.width() - factor * wr) // 2
        rem_h = (image.height() - factor * hr) // 2
        image = image.copy(rem_w, rem_h, factor * wr, factor * hr)

        if logo_data is not None:
            logo = QImage()
            logo.loadFromData(logo_data)
            logo.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
            if logo.width() > image.width():
                logo = logo.scaled(
                    image.width(),
                    image.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            painter = QPainter(image)
            painter.drawImage(
                (image.width() - logo.width()) // 2,
                image.height() - logo.height(),
                logo,
            )
            painter.end()

        return image.scaled(
            preset.size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _convert_icon(self, cover: QImage) -> QImage:
        icon_size = QSize(128, 128)
        icon = QImage(icon_size, QImage.Format.Format_ARGB32_Premultiplied)
        painter = QPainter(icon)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(icon.rect(), Qt.GlobalColor.transparent)
        overlay = self._generate_icon_overlay(icon.rect())
        brush = QBrush(cover)
        scale = max(icon.width() / cover.width(), icon.height() / cover.height())
        transform = QTransform().scale(scale, scale)
        brush.setTransform(transform)
        painter.fillPath(overlay, brush)
        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)
        painter.drawPath(overlay)
        painter.end()
        return icon

    def _save_image(self, image: QImage, color_path: Path, gray_path: Path):
        # this is not required if we ever want to re-apply the alpha channel
        # image = image.convertToFormat(QImage.Format_Indexed8)
        # add the alpha channel back to the cover
        image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        image.save(color_path.as_posix(), format="PNG")
        # quick way to convert to grayscale, but keep the alpha channel
        alpha = image.convertToFormat(QImage.Format.Format_Alpha8)
        image = image.convertToFormat(QImage.Format.Format_Grayscale8)
        # add the alpha channel back to the grayscale cover
        image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        image.setAlphaChannel(alpha)
        image.save(gray_path.as_posix(), format="PNG")

    def _convert(self, game, images, force=False) -> None:
        for file in self._img_all(game.app_name):
            if force and file.exists():
                file.unlink(missing_ok=True)

        def find_image_data(image_types: Tuple):
            data = None
            for image_type in image_types:
                if images.get(image_type, None) is not None:
                    data = images[image_type]
                    break
            return data

        tall_data = find_image_data(self._img_tall_types)
        wide_data = find_image_data(self._img_wide_types)
        logo_data = find_image_data(self._img_logo_types)

        icon_source = "wide" if tall_data is None else "tall"

        if tall_data is None and wide_data is not None:
            tall_data = wide_data

        if wide_data is None and tall_data is not None:
            wide_data = tall_data

        tall = self._convert_image(tall_data, logo_data, ImageSize.Tall)
        self._save_image(
            tall,
            image_tall_path(game.app_name),
            image_tall_path(game.app_name, color=False),
        )

        wide = self._convert_image(wide_data, logo_data, ImageSize.Wide)
        self._save_image(
            wide,
            image_wide_path(game.app_name),
            image_wide_path(game.app_name, color=False),
        )

        icon = self._convert_icon(tall if icon_source == "tall" else wide)
        self._save_image(
            icon,
            image_icon_path(game.app_name),
            image_icon_path(game.app_name, color=False),
        )
        icon.save(
            desktop_icon_path(game.app_name).as_posix(),
            format=desktop_icon_suffix().upper(),
        )

    def _compress(self, game: Game, data: Dict) -> None:
        archive = open(self._img_cache(game.app_name), "wb")
        cdata = zlib.compress(pickle.dumps(data), level=-1)
        archive.write(cdata)
        archive.close()

    def _decompress(self, game: Game) -> Dict:
        archive = open(self._img_cache(game.app_name), "rb")
        try:
            data = zlib.decompress(archive.read())
            data = pickle.loads(data)
        except zlib.error:
            data = dict(zip(self._img_types, [None] * len(self._img_types)))
        finally:
            archive.close()
        return data

    def _append_to_worker_queue(self, game: Game):
        self._worker_lock.acquire()
        try:
            self._worker_app_names.add(game.app_name)
        finally:
            self._worker_lock.release()

    @Slot(object)
    def _remove_from_worker_queue(self, game: Game):
        self._worker_lock.acquire()
        try:
            self._worker_app_names.remove(game.app_name)
        finally:
            self._worker_lock.release()

    def _download_image(self, game, force: bool):
        updates, json_data = self._prepare_download(game, force)
        if updates:
            self._download(updates, json_data, game)
        self.logger.debug("Emitting singal for %s (%s)", game.app_name, game.app_title)

    def download_image(self, game: Game, load_callback: Callable[[], None], priority: int, force: bool = False) -> None:
        if game.app_name in self._worker_app_names:
            return
        self._append_to_worker_queue(game)
        image_worker = ImageWorker(self._download_image, game, force)
        image_worker.signals.completed.connect(load_callback)
        image_worker.signals.completed.connect(self._remove_from_worker_queue)
        self.threadpool.start(image_worker, priority)

    def download_image_launch(self, game: Game, callback: Callable[[Game], None], priority: int, force: bool = False) -> None:
        if self.has_pixmaps(game.app_name) and not force:
            return

        def _callback():
            callback(game)

        self.download_image(game, _callback, priority, force)

    def download_image_blocking(self, game: Game, load_callback: Callable[[], None], priority: int, force: bool = False) -> None:
        self._append_to_worker_queue(game)
        self._download_image(game, force)
        load_callback()
        self._remove_from_worker_queue(game)

    @staticmethod
    def _get_cover(
        container: Union[Type[QPixmap], Type[QImage]],
        app_name: str,
        preset: ImageSize.Preset,
        color: bool,
    ) -> Union[QPixmap, QImage]:
        ret = container()
        if preset.orientation == ImageType.Icon:
            if image_icon_path(app_name, color).is_file():
                ret.load(image_icon_path(app_name, color).as_posix())
        elif preset.orientation == ImageType.Tall:
            if image_tall_path(app_name, color).is_file():
                ret.load(image_tall_path(app_name, color).as_posix())
        elif preset.orientation == ImageType.Wide:
            if image_wide_path(app_name, color).is_file():
                ret.load(image_wide_path(app_name, color).as_posix())
        else:
            raise RuntimeError("Unknown image preset")
        if not ret.isNull():
            device = ImageSize.Preset(
                divisor=preset.base.divisor,
                pixel_ratio=1,
                orientation=preset.base.orientation,
                base=preset,
            )
            ret.setDevicePixelRatio(preset.pixel_ratio)
            # lk: Scaling happens at painting. It might be inefficient so leave this here as an alternative
            # lk: If this is uncommented, the transformation in ImageWidget should be adjusted too
            ret = ret.scaled(
                device.size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            ret.setDevicePixelRatio(device.pixel_ratio)
        return ret

    def get_pixmap(self, app_name: str, preset: ImageSize.Preset, color: bool = True) -> QPixmap:
        """
        Use when the image is to be presented directly on the screen.

        @param app_name: The RareGame object for this game
        @param preset:
        @param color: True to load the colored pixmap, False to load the grayscale
        @return: QPixmap
        """
        pixmap: QPixmap = self._get_cover(QPixmap, app_name, preset, color)
        return pixmap

    def get_image(self, app_name: str, preset: ImageSize.Preset, color: bool = True) -> QImage:
        """
        Use when the image has to be manipulated before being rendered.

        @param app_name: The RareGame object for this game
        @param preset:
        @param color: True to load the colored image, False to load the grayscale
        @return: QImage
        """
        image: QImage = self._get_cover(QImage, app_name, preset, color)
        return image
