from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from typing import Optional

from dataclass_wizard.v0 import YAMLWizard
from mediascan.types.config.mediascan_config_loader import load_mediascan_config_file

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MediaTestConfig(YAMLWizard):
    minimum_filesize: int
    mediatest_rootdir: Optional[str] = None
    log_throttle_seconds: Optional[float] = None


@dataclass(frozen=True)
class RuntimeConfig:
    media_test_config: MediaTestConfig
    media_rootdir: str
    mediatest_rootdir: str
    mediascan_db_path: str
    exts_media: tuple[str, ...]
    exts_art: tuple[str, ...]
    exts_lyrics: tuple[str, ...]
    exts_metadata: tuple[str, ...]
    exts_extra: tuple[str, ...]
    allowed_exts: tuple[str, ...]
    minimum_filesize: int
    lib_count: int
    libs_media_path: tuple[str, ...]
    log_throttle_seconds: float | None


class MediaTestConfigUtil:
    """Utility class for loading mediatest configuration from YAML."""

    yaml_filename = "mediatest-config.yml"

    def load_config(self, path: Path) -> MediaTestConfig:
        config_path = Path(path)
        logger.debug("Attempting to load mediatest config from %s", config_path)
        if not config_path.is_file():
            raise FileNotFoundError(f"Mediatest config file not found: {config_path}")

        with config_path.open("r", encoding="utf-8") as config_file:
            config = MediaTestConfig.from_yaml(  # pyright: ignore[reportUnknownMemberType]
                config_file
            )
        if isinstance(config, list):
            logger.debug(
                "Parsed YAML returned a list with %d item(s); selecting first entry",
                len(config),
            )
            config = config[0]

        logger.info("Loaded mediatest config from %s", config_path)
        return config


_runtime_config: RuntimeConfig | None = None


def get_config() -> RuntimeConfig:
    if _runtime_config is None:
        raise RuntimeError("Mediatest has not been configured")
    return _runtime_config


def configure(collection_rootdir: Path) -> RuntimeConfig:
    global _runtime_config

    collection_rootdir = collection_rootdir.expanduser().resolve()
    if not collection_rootdir.is_dir():
        raise NotADirectoryError(
            f"Moongas collection root is not a directory: {collection_rootdir}"
        )

    mediatest_config_path = collection_rootdir / MediaTestConfigUtil.yaml_filename
    mediascan_config_path = collection_rootdir / "mediascan-config.yml"
    logger.info("Loading collection configuration from %s", collection_rootdir)
    try:
        media_test_config = MediaTestConfigUtil().load_config(mediatest_config_path)
        mediascan_config = load_mediascan_config_file(mediascan_config_path)
    except Exception:
        logger.exception(
            "configure() failed while loading collection configs from %s",
            collection_rootdir,
        )
        raise

    media_rootdir = str(collection_rootdir)
    if media_test_config.mediatest_rootdir is not None:
        mediatest_rootdir = Path(media_test_config.mediatest_rootdir).expanduser()
        if not mediatest_rootdir.is_absolute():
            mediatest_rootdir = collection_rootdir / mediatest_rootdir
        resolved_mediatest_rootdir = str(mediatest_rootdir.resolve())
    else:
        resolved_mediatest_rootdir = str(
            collection_rootdir / "moongas-mediatest-python-pytest"
        )

    exts_media = tuple(
        extension.lstrip(".") for extension in mediascan_config.media_exts
    )
    exts_art = ("jpg", "webp", "png", "xcf")
    exts_lyrics = ("lrc", "txt")
    exts_metadata = ("yml",)
    exts_extra = ("pdf",)
    allowed_exts = exts_media + exts_art + exts_lyrics + exts_metadata + exts_extra
    libs_media_path: list[str] = []
    for media_dir in mediascan_config.media_dirs:
        media_path = Path(media_dir).expanduser()
        if not media_path.is_absolute():
            media_path = collection_rootdir / media_path
        resolved_media_path = str(media_path.resolve())
        libs_media_path.append(resolved_media_path)
        logger.info(
            "Resolved media directory: configured=%s resolved=%s",
            media_dir,
            resolved_media_path,
        )

    runtime_config = RuntimeConfig(
        media_test_config=media_test_config,
        media_rootdir=media_rootdir,
        mediatest_rootdir=resolved_mediatest_rootdir,
        mediascan_db_path=str(collection_rootdir / "mediascan.db"),
        exts_media=exts_media,
        exts_art=exts_art,
        exts_lyrics=exts_lyrics,
        exts_metadata=exts_metadata,
        exts_extra=exts_extra,
        allowed_exts=allowed_exts,
        minimum_filesize=media_test_config.minimum_filesize,
        lib_count=len(mediascan_config.media_dirs),
        libs_media_path=tuple(libs_media_path),
        log_throttle_seconds=media_test_config.log_throttle_seconds,
    )
    _runtime_config = runtime_config

    logger.info(
        "Configured %d media directories from %s; mediatest_rootdir=%s "
        "mediascan_db_path=%s minimum_filesize=%s",
        runtime_config.lib_count,
        mediascan_config_path,
        runtime_config.mediatest_rootdir,
        runtime_config.mediascan_db_path,
        runtime_config.minimum_filesize,
    )
    logger.debug(
        "Configured extensions: media=%s art=%s lyrics=%s metadata=%s extra=%s",
        runtime_config.exts_media,
        runtime_config.exts_art,
        runtime_config.exts_lyrics,
        runtime_config.exts_metadata,
        runtime_config.exts_extra,
    )
    logger.debug("Resolved media directories: %s", runtime_config.libs_media_path)
    return runtime_config


PRESENT_YEAR: int = datetime.now().year
