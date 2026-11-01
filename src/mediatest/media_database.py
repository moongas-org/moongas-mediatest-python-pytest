import logging
from pathlib import Path
import sqlite3

from mediascan.utils.db.mediafile.mediafile_data_with_album_and_artist_data import (
    MediaFileDataWithAlbumAndArtistData,
    row_to_mediafile_data_with_album_and_artist_data,
)
from mediascan.utils.db.track.track_data_with_album_and_artist_data import (
    TrackDataWithAlbumAndArtistData,
    row_to_track_data_with_album_and_artist_data,
)
from mediascan.utils.db.mediascan_db_loader import (
    get_df_mediafile_track_album_artist_joined,
    get_df_track_album_artist_joined,
)
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


def load_database_mediafiles(db_path: Path) -> list[MediaFileDataWithAlbumAndArtistData]:
    db_path = db_path.expanduser().resolve()
    if not db_path.is_file():
        raise FileNotFoundError(f"Mediascan database not found: {db_path}")

    logger.info("Loading mediafiles with track, album, and artist data from %s", db_path)
    engine = create_engine(
        "sqlite://",
        creator=lambda: sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True),
    )
    try:
        mediafiles = get_df_mediafile_track_album_artist_joined(engine)
        result = [
            row_to_mediafile_data_with_album_and_artist_data(row)
            for _, row in mediafiles.iterrows()
        ]
        for mediafile in result:
            media_path = Path(mediafile.path)
            if not media_path.is_absolute():
                mediafile.path = str(db_path.parent / media_path)
    except Exception:
        logger.exception("Failed to load mediascan database from %s", db_path)
        raise
    finally:
        engine.dispose()

    logger.info("Loaded %d mediafiles from %s", len(result), db_path)
    return result


def load_database_tracks(db_path: Path) -> list[TrackDataWithAlbumAndArtistData]:
    db_path = db_path.expanduser().resolve()
    if not db_path.is_file():
        raise FileNotFoundError(f"Mediascan database not found: {db_path}")

    logger.info("Loading tracks with album and artist data from %s", db_path)
    engine = create_engine(
        "sqlite://",
        creator=lambda: sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True),
    )
    try:
        tracks = get_df_track_album_artist_joined(engine)
        result = [
            row_to_track_data_with_album_and_artist_data(row)
            for _, row in tracks.iterrows()
        ]
        for track in result:
            track_path = Path(track.path)
            if not track_path.is_absolute():
                track.path = str(db_path.parent / track_path)
    except Exception:
        logger.exception("Failed to load mediascan database from %s", db_path)
        raise
    finally:
        engine.dispose()

    logger.info("Loaded %d tracks from %s", len(result), db_path)
    return result
