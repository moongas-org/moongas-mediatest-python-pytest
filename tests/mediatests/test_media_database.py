from pathlib import Path
from typing import Optional

import pytest
from mediascan.utils.db.mediafile.mediafile_data_with_album_and_artist_data import MediaFileDataWithAlbumAndArtistData

from mediatest.config import PRESENT_YEAR, get_config
from mediatest.media_database import load_database_mediafiles

_FILES_KEY = pytest.StashKey[list[MediaFileDataWithAlbumAndArtistData]]()


def database_mediafiles(config: pytest.Config) -> list[MediaFileDataWithAlbumAndArtistData]:
    if _FILES_KEY not in config.stash:
        config.stash[_FILES_KEY] = load_database_mediafiles(Path(get_config().mediascan_db_path))
    return config.stash[_FILES_KEY]


NO_ERRORS = "(no errors)"


@pytest.fixture(scope="session")
def files(pytestconfig: pytest.Config) -> list[MediaFileDataWithAlbumAndArtistData]:
    return database_mediafiles(pytestconfig)


def run_tests(files: list[MediaFileDataWithAlbumAndArtistData]) -> list[str]:
    errors: list[str] = []
    errors += run_test_mediafile(files, "artist")
    errors += run_test_mediafile(files, "albumartist")
    errors += run_test_mediafile(files, "album", "albumartist")
    return errors


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Indirect parametrization for pytest to run
    test_per_error for each error found.
    parametrizes with a list of errors or [NO_ERRORS]
    i.e. the length of the list is at least 1
    (the sentinel value element NO_ERRORS allows
    at least one test to run and pass,
    otherwise the test would just be greyed out)
    """
    if "file" in metafunc.fixturenames:
        mediafiles = database_mediafiles(metafunc.config)
        metafunc.parametrize("file", mediafiles, ids=[str(file.id) for file in mediafiles])
    if "error" in metafunc.fixturenames:
        errors = run_tests(database_mediafiles(metafunc.config))
        if len(errors) == 0:
            errors.append(NO_ERRORS)
        metafunc.parametrize("error", errors)


def test_per_error(error: str):
    """Test that fails for each error found.
    If there are no errors, it will run once and pass.
    Works with pytest using indirect parametrization.
    (See pytest_generate_tests above)
    """
    assert error == NO_ERRORS


def test_mediafile_year_gt_zero(file: MediaFileDataWithAlbumAndArtistData):
    assert file.year is not None and file.year > 0, f"{file.path}"


def test_mediafile_years_lt_present(file: MediaFileDataWithAlbumAndArtistData):
    assert file.year is not None and file.year <= PRESENT_YEAR, f"{file.path}"


def test_mediafile_size_gt_min(file: MediaFileDataWithAlbumAndArtistData):
    assert Path(file.path).stat().st_size >= get_config().minimum_filesize, file.path


def test_mediafile_artist_is_not_empty(file: MediaFileDataWithAlbumAndArtistData):
    assert file.artist, f"{file.path}"


def test_mediafile_albumartist_is_not_empty(file: MediaFileDataWithAlbumAndArtistData):
    assert file.albumartist, f"{file.path}"


def test_mediafile_albumartist_same_for_every_track_in_every_album(
    files: list[MediaFileDataWithAlbumAndArtistData],
):
    """
    Different tracks may have different artists e.g. "Dr. Dre feat. Snoop Dog"
    but all tracks in a an albums should have the same albumartist e.g. "Dr. Dre"
    """
    albums: dict[str, str] = {}
    for file in files:
        assert file.albumartist, file.path
        albumkey = str(Path(file.path).parent)
        if albumkey in albums:
            assert albums[albumkey] == file.albumartist
        else:
            albums[albumkey] = file.albumartist


def escape_artist_name(name: str):
    """
    Escape artist/albumartist name according to rules used for moongas artist directory names
    E.g. "Dr. Dre" becomes "Dr_ Dre"
    """
    return name.replace(".", "_")


def test_mediafile_albumartist_matches_artist_directory_name(
    files: list[MediaFileDataWithAlbumAndArtistData],
):
    """
    Different tracks may have different artists e.g. "Dr. Dre feat. Snoop Dog"
    but all tracks under a given artist folder e.g. "Dr_ Dre" should have the same albumartist e.g. "Dr. Dre"
    and it should match the artist directory name (after escaping)
    """
    artists: dict[str, str] = {}
    for file in files:
        assert file.albumartist, file.path
        albumartist_escaped = escape_artist_name(file.albumartist)
        artist_dir = Path(file.path).parent.parent
        assert artist_dir.name == albumartist_escaped, (
            f"File (path={file.path}) albumartist '{file.albumartist}' "
            f"(escaped={albumartist_escaped}) does not match artist directory name '{artist_dir.name}'"
        )
        key = str(artist_dir)
        if key in artists:
            assert artists[key] == albumartist_escaped, file.path
        else:
            artists[key] = albumartist_escaped


def run_test_mediafile(
    files: list[MediaFileDataWithAlbumAndArtistData], tag_type: str, tag_type_2: Optional[str] = None
) -> list[str]:
    """
    tag_type: the tag to test
    tag_type_2: optional secondary qualifier, makes it skip validation if tag_type_2
    doesn't match. E.g. tag_type="album" and tag_type_2="artist" => only compare
    two albums if the artist is the same for both of them.
    """
    errors: list[str] = []
    grouped: dict[str, list[MediaFileDataWithAlbumAndArtistData]] = {}
    for file in files:
        key = str(getattr(file, tag_type)).upper()
        if key in grouped:
            grouped[key].append(file)
        else:
            grouped[key] = [file]
    for _, v_l in grouped.items():
        f0 = v_l[0]
        for f in v_l[1:]:
            v1 = getattr(f, tag_type)
            v2 = getattr(f0, tag_type)
            if v1 != v2:
                if tag_type_2 is not None:
                    v2_1 = getattr(f0, tag_type_2)
                    v2_2 = getattr(f, tag_type_2)
                    if v2_1 != v2_2:
                        # e.g. albums with different capitalizaiton but different albumartists
                        # so it doesn't really matter so much
                        continue
                errors.append(
                    f"{tag_type.capitalize()} {f.artist} - {f.album} - {f.title} "
                    + f"tagged with inconsistent case-sensitivity ({v1} != {v2}) "
                    + f"\nf1={f0}\nf2={f}"
                )
    return errors
