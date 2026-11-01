import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from sqlalchemy.exc import NoSuchTableError
from mediascan.types.media_file.media_file_data_with_album_and_artist_data import MediaFileDataWithAlbumAndArtistData
from mediascan.types.track.track_data_with_album_and_artist_data import TrackDataWithAlbumAndArtistData

from mediatest.media_database import load_database_media_files, load_database_tracks


@pytest.fixture
def database(tmp_path: Path) -> Path:
    db_path = tmp_path / "mediascan.db"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE track (
                id INTEGER PRIMARY KEY, path TEXT, title TEXT, artist TEXT,
                albumartist TEXT, album TEXT, genre TEXT, year INTEGER, artistid INTEGER, albumid INTEGER
            );
            CREATE TABLE mediafile (
                id INTEGER PRIMARY KEY, trackid INTEGER, path TEXT, title TEXT,
                artist TEXT, albumartist TEXT, album TEXT, genre TEXT, year INTEGER
            );
            CREATE TABLE album (id INTEGER PRIMARY KEY, path TEXT, year INTEGER, genre TEXT);
            CREATE TABLE artist (
                id INTEGER PRIMARY KEY, path TEXT, countrycode TEXT,
                regioncode TEXT, city TEXT, languagecode TEXT
            );
            INSERT INTO album VALUES (2, 'Music/Artist/Album', 1999, 'Jazz');
            INSERT INTO artist VALUES (1, 'Music/Artist', 'US', 'CO', 'Denver', 'en');
            INSERT INTO track VALUES
                (10, 'Music/Artist/Album/Song.yml', 'Track title', 'Artist', 'Artist', 'Album', 'Rock', 2020, 1, 2),
                (20, 'Music/Artist/Album/Stream.yml', 'Stream', 'Artist', 'Artist', 'Album', 'Rock', 2021, 1, 2);
            INSERT INTO mediafile VALUES
                (99, 10, 'Music/Artist/Album/Song.mp3', 'Song', 'Artist', 'Artist', 'Album', 'Rock', 2020),
                (3, 10, 'Music/Artist/Album/Song.flac', 'Song', 'Artist', 'Artist', 'Album', 'Rock', 2020);
            """
        )
    for suffix in ("mp3", "flac"):
        media_path = tmp_path / f"Music/Artist/Album/Song.{suffix}"
        media_path.parent.mkdir(parents=True, exist_ok=True)
        media_path.write_bytes(b"x" * 123)
    return db_path


def test_load_mediafiles_with_joined_data(database: Path) -> None:
    files = load_database_media_files(database)
    assert isinstance(files, list)
    assert len(files) == 2
    assert all(isinstance(file, MediaFileDataWithAlbumAndArtistData) for file in files)
    assert {file.id for file in files} == {99, 3}
    local = files[0]
    assert local.title == "Song"
    assert local.artist == local.albumartist == "Artist"
    assert local.album == "Album"
    assert local.year == 2020
    assert {file.path for file in files} == {
        str(database.parent / "Music/Artist/Album/Song.mp3"),
        str(database.parent / "Music/Artist/Album/Song.flac"),
    }
    assert local.album_path == "Music/Artist/Album"
    assert local.artist_path == "Music/Artist"
    assert local.countryCode == "US"
    assert local.regionCode == "CO"
    assert local.city == "Denver"
    assert local.languageCode == "en"
    assert local.size is None


def test_absolute_media_path_is_preserved(database: Path) -> None:
    absolute_path = str(database.parent / "Other/Song.mp3")
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE mediafile SET path = ? WHERE id = 99", (absolute_path,))
    assert absolute_path in {file.path for file in load_database_media_files(database)}


def test_load_tracks_with_joined_data(database: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TABLE mediafile")
    tracks = load_database_tracks(database)
    assert isinstance(tracks, list)
    assert len(tracks) == 2
    assert all(isinstance(track, TrackDataWithAlbumAndArtistData) for track in tracks)
    assert {track.id for track in tracks} == {10, 20}
    track = next(track for track in tracks if track.id == 10)
    assert track.title == "Track title"
    assert track.artist == track.albumartist == "Artist"
    assert track.album == "Album"
    assert track.genre == "Rock"
    assert track.year == 2020
    assert {track.path for track in tracks} == {
        str(database.parent / "Music/Artist/Album/Song.yml"),
        str(database.parent / "Music/Artist/Album/Stream.yml"),
    }
    assert track.album_path == "Music/Artist/Album"
    assert track.artist_path == "Music/Artist"
    assert track.countryCode == "US"
    assert track.regionCode == "CO"
    assert track.city == "Denver"
    assert track.languageCode == "en"


def test_absolute_track_path_is_preserved(database: Path) -> None:
    absolute_path = str(database.parent / "Other/Song.yml")
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE track SET path = ? WHERE id = 10", (absolute_path,))
    assert absolute_path in {track.path for track in load_database_tracks(database)}


def test_track_year_and_genre_are_used_when_album_columns_overlap(database: Path) -> None:
    track = next(track for track in load_database_tracks(database) if track.id == 10)
    assert track.year == 2020
    assert track.genre == "Rock"


def test_empty_tracks(database: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute("DELETE FROM track")
    assert load_database_tracks(database) == []


@pytest.mark.parametrize("reference", [None, 999])
def test_unlinked_track_is_included(database: Path, reference: int | None) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE track SET artistid = ?, albumid = ? WHERE id = 10",
            (reference, reference),
        )
    tracks = load_database_tracks(database)
    assert {track.id for track in tracks} == {10, 20}
    assert next(track for track in tracks if track.id == 10).title == "Track title"


@pytest.mark.parametrize("tracks", [False, True])
def test_missing_database_is_not_created(tmp_path: Path, tracks: bool) -> None:
    database = tmp_path / "mediascan.db"
    loader = load_database_tracks if tracks else load_database_media_files
    with pytest.raises(FileNotFoundError, match="Mediascan database not found"):
        loader(database)
    assert not database.exists()


@pytest.mark.parametrize("table", ["mediafile", "track"])
def test_missing_database_table_raises(database: Path, table: str) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute(f"DROP TABLE {table}")
    loader = load_database_tracks if table == "track" else load_database_media_files
    with pytest.raises(NoSuchTableError, match=table):
        loader(database)


def test_broken_track_reference_preserves_mediafile(database: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE mediafile SET trackid = 999 WHERE id = 99")
    files = load_database_media_files(database)
    file = next(file for file in files if file.id == 99)
    assert file.title == "Song"
    assert file.album_path is None
    assert file.artist_path is None


def test_unlinked_mediafile_is_included(database: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE mediafile SET trackid = NULL WHERE id = 99")
    files = load_database_media_files(database)
    assert {file.id for file in files} == {99, 3}
    file = next(file for file in files if file.id == 99)
    assert file.artist == "Artist"
    assert file.countryCode is None


@pytest.mark.parametrize("failure", [None, "missing", "undersized", "mediafile_metadata", "database"])
def test_database_media_tests(database: Path, failure: str | None) -> None:
    collection = database.parent
    (collection / "mediatest-config.yml").write_text("minimumFilesize: 123\n", encoding="utf-8")
    (collection / "mediascan-config.yml").write_text(
        "mediaDirs: [Music]\nmediaExts: [.mp3, .flac]\n", encoding="utf-8"
    )
    if failure == "missing":
        (collection / "Music/Artist/Album/Song.flac").unlink()
    elif failure == "undersized":
        (collection / "Music/Artist/Album/Song.flac").write_bytes(b"x" * 122)
    elif failure == "mediafile_metadata":
        with sqlite3.connect(database) as connection:
            connection.execute("UPDATE mediafile SET year = NULL WHERE id = 99")
    elif failure == "database":
        database.unlink()
    test_path = Path(__file__).resolve().parents[1] / "mediatests/test_media_database.py"
    source_path = str(test_path.parents[2] / "src")
    pythonpath = os.pathsep.join(filter(None, (source_path, os.environ.get("PYTHONPATH"))))
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from pathlib import Path; import pytest; "
            "from mediatest.config import configure; configure(Path(sys.argv[1])); "
            "sys.exit(pytest.main([sys.argv[2], '-o', 'addopts=', '-q']))",
            str(collection),
            str(test_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": pythonpath},
    )
    if failure == "database":
        assert result.returncode == 2, result.stdout + result.stderr
        assert "Mediascan database not found" in result.stdout
        assert not database.exists()
    elif failure is not None:
        assert result.returncode == 1, result.stdout + result.stderr
        expected_error = {
            "missing": "FileNotFoundError",
            "undersized": "test_mediafile_size_gt_min[3]",
            "mediafile_metadata": "test_mediafile_year_gt_zero[99]",
        }
        assert expected_error[failure] in result.stdout
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "13 passed" in result.stdout
