from dataclasses import dataclass
from datetime import datetime
import logging
import os
from pathlib import Path
import sys
from typing import Optional

from dataclass_wizard.v0 import YAMLWizard
from mediascan.genres import Genre

logger = logging.getLogger(__name__)


@dataclass
class MediaTestLibConfig(YAMLWizard):
    media_path: str
    expected_media_count: int
    expected_lrc_count: int
    total_filesize_limit_gb: int
    expected_filesize_gb: int
    genres: list[Genre]


@dataclass
class MediaTestConfig(YAMLWizard):
    minimum_filesize: int
    exts_media: list[str]
    exts_art: list[str]
    exts_lyrics: list[str]
    exts_metadata: list[str]
    exts_extra: list[str]
    lib_genres_mode_blacklist: bool
    libs: list[MediaTestLibConfig]
    mediascan_files_yaml_path: Optional[str] = None

    mediatest_rootdir: Optional[str] = None
    media_rootdir: Optional[str] = None
    log_throttle_seconds: Optional[float] = None


class MediaTestConfigUtil:
    """Utility class for loading mediatest configuration from YAML."""

    yaml_filename = "mediatest-config.yml"

    def load_config(self, path: Path | None = None) -> MediaTestConfig:
        logger.debug("load_config() called with path=%s, cwd=%s", path, os.getcwd())
        if path is not None:
            config_path = Path(path)
            logger.debug(
                "Attempting to load config from explicit path: %s", config_path
            )
            if not config_path.exists():
                raise Exception(
                    f"The provided mediatest config file path does not exist: path={path} cwd={os.getcwd()}"
                )
            logger.debug("Explicit config path exists: %s", config_path)
        else:
            source_config_path = (
                Path(__file__).resolve().parents[2] / self.yaml_filename
            )
            fallback_config_path = Path(sys.prefix) / self.yaml_filename
            logger.debug(
                "No explicit path provided; checking default config locations: source=%s fallback=%s",
                source_config_path,
                fallback_config_path,
            )
            config_path = (
                source_config_path
                if source_config_path.exists()
                else fallback_config_path
            )
            logger.debug("Using default config path: %s", config_path)

        logger.debug("Opening config file for parsing: %s", config_path)
        with config_path.open("r", encoding="utf-8") as config_file:
            config = (
                MediaTestConfig.from_yaml(  # pyright: ignore[reportUnknownMemberType]
                    config_file
                )
            )
        if isinstance(config, list):
            logger.debug(
                "Parsed YAML returned a list with %d item(s); selecting first entry",
                len(config),
            )
            config = config[0]

        logger.info("Loaded config from %s", config_path)
        logger.debug(
            "Config summary: mediatest_rootdir=%s libs=%d mediascan_files_yaml_path=%s minimum_filesize=%s",
            getattr(config, "mediatest_rootdir", None),
            len(config.libs),
            config.mediascan_files_yaml_path,
            config.minimum_filesize,
        )
        return config


def configure(path: Path | None = None) -> None:
    global CONFIG
    global MEDIATEST_ROOTDIR, MEDIA_ROOTDIR
    global MEDIASCAN_FILES_YAML_PATH
    global EXTS_MEDIA, EXTS_ART, EXTS_LYRICS, EXTS_METADATA, EXTS_EXTRA, ALLOWED_EXTS
    global MINIMUM_FILESIZE
    global LIB_GENRES_MODE_BLACKLIST, LIB_COUNT, LIBS_MEDIA_PATH
    global LIBS_EXPECTED_MEDIA_COUNT, LIBS_EXPECTED_LRC_COUNT
    global LIBS_TOTAL_FILESIZE_LIMIT_GB, LIBS_EXPECTED_FILESIZE_GB, LIBS_GENRES
    global LOG_THROTTLE_SECONDS

    logger.info("configure() starting; path=%s", path)
    try:
        CONFIG = MediaTestConfigUtil().load_config(path)
    except Exception:
        logger.exception("configure() failed while loading config from %s", path)
        raise

    logger.debug("Config object loaded; assigning global configuration values")
    MEDIATEST_ROOTDIR = CONFIG.mediatest_rootdir
    MEDIA_ROOTDIR = CONFIG.media_rootdir
    MEDIASCAN_FILES_YAML_PATH = CONFIG.mediascan_files_yaml_path
    MINIMUM_FILESIZE = CONFIG.minimum_filesize
    EXTS_MEDIA = CONFIG.exts_media
    EXTS_ART = CONFIG.exts_art
    EXTS_LYRICS = CONFIG.exts_lyrics
    EXTS_METADATA = CONFIG.exts_metadata
    EXTS_EXTRA = CONFIG.exts_extra
    ALLOWED_EXTS = EXTS_MEDIA + EXTS_ART + EXTS_LYRICS + EXTS_METADATA + EXTS_EXTRA
    LIB_GENRES_MODE_BLACKLIST = CONFIG.lib_genres_mode_blacklist
    LIB_COUNT = len(CONFIG.libs)
    LOG_THROTTLE_SECONDS = CONFIG.log_throttle_seconds

    media_rootdir = (
        Path(CONFIG.media_rootdir).expanduser().resolve()
        if CONFIG.media_rootdir is not None
        else None
    )
    if media_rootdir is not None:
        logger.info(
            "Resolving library media paths relative to mediaRootDir=%s", media_rootdir
        )
    resolved_media_paths: list[str] = []
    for lib in CONFIG.libs:
        media_path = Path(lib.media_path.lstrip("/\\"))
        resolved_media_path = (
            str(media_rootdir / media_path)
            if media_rootdir is not None
            else lib.media_path
        )
        resolved_media_paths.append(resolved_media_path)
        logger.info(
            "Resolved library media path: configured=%s resolved=%s",
            lib.media_path,
            resolved_media_path,
        )
    LIBS_MEDIA_PATH = resolved_media_paths
    LIBS_EXPECTED_MEDIA_COUNT = [lib.expected_media_count for lib in CONFIG.libs]
    LIBS_EXPECTED_LRC_COUNT = [lib.expected_lrc_count for lib in CONFIG.libs]
    LIBS_TOTAL_FILESIZE_LIMIT_GB = [lib.total_filesize_limit_gb for lib in CONFIG.libs]
    LIBS_EXPECTED_FILESIZE_GB = [lib.expected_filesize_gb for lib in CONFIG.libs]
    LIBS_GENRES = [lib.genres for lib in CONFIG.libs]

    logger.info(
        "configure() completed for %d libraries; mediatest_rootdir=%s media_rootdir=%s mediascan_files_yaml_path=%s minimum_filesize=%s",
        LIB_COUNT,
        MEDIATEST_ROOTDIR,
        MEDIA_ROOTDIR,
        MEDIASCAN_FILES_YAML_PATH,
        MINIMUM_FILESIZE,
    )
    logger.debug(
        "Configured extensions: media=%s art=%s lyrics=%s metadata=%s extra=%s",
        EXTS_MEDIA,
        EXTS_ART,
        EXTS_LYRICS,
        EXTS_METADATA,
        EXTS_EXTRA,
    )
    logger.debug("Library media paths: %s", LIBS_MEDIA_PATH)


PRESENT_YEAR: int = datetime.now().year
configure()
