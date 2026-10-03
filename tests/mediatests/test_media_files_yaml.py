from pathlib import Path
from typing import Callable, Optional, cast

import pytest
from mediascan.genres import Genre
from mediascan.media_file_data import MediaFileData
from mediascan.media_files_yaml_file_loader import load_media_files_yaml_file

from mediatest.media_utils import get_all_genre_strings

"""
These tests are dependant on the mediascan-files.yml file.
These tests can be skipped by configuring mediascanFilesYamlPath to 'null' 
(or removing it from mediatest-config.yml)
Some of these tests also examine the filesytem (e.g. verifying the paths in mediascan-files.yml exist)
"""

from mediatest.config import (
    LIB_COUNT,
    LIB_GENRES_MODE_BLACKLIST,
    LIBS_GENRES,
    LIBS_MEDIA_PATH,
    MEDIASCAN_FILES_YAML_PATH,
    MINIMUM_FILESIZE,
    PRESENT_YEAR,
)


def load_yaml_media_files() -> list[MediaFileData]:
    if MEDIASCAN_FILES_YAML_PATH is None:
        return []
    try:
        return load_media_files_yaml_file(MEDIASCAN_FILES_YAML_PATH).files
    except (FileNotFoundError, OSError):
        return []


@pytest.fixture(scope="session")
def files() -> list[MediaFileData]:
    return load_yaml_media_files()


def media_file_indices() -> list[int]:
    return list(range(len(load_yaml_media_files())))


def media_file_parametrize(func: Callable[..., None]) -> Callable[..., None]:
    decorator = pytest.mark.parametrize("file", media_file_indices(), indirect=True)
    return decorator(func)


# Helper fixture to extract individual files from your session fixture
@pytest.fixture
def file(request: pytest.FixtureRequest, files: list[MediaFileData]) -> MediaFileData:
    # request.param will be the index of the file
    index = cast(int, request.param)
    return files[index]


NO_ERRORS = "(no errors)"


def run_tests() -> list[str]:
    errors: list[str] = []
    errors += run_test_mediafile("artist")
    errors += run_test_mediafile("albumartist")
    errors += run_test_mediafile("album", "albumartist")
    return errors


def pytest_generate_tests(metafunc):  # type: ignore
    """Indirect parametrization for pytest to run
    test_per_error for each error found.
    parametrizes with a list of errors or [NO_ERRORS]
    i.e. the length of the list is at least 1
    (the sentinel value element NO_ERRORS allows
    at least one test to run and pass,
    otherwise the test would just be greyed out)
    """
    if "error" in metafunc.fixturenames:  # type: ignore
        errors = run_tests()
        if len(errors) == 0:
            errors.append(NO_ERRORS)
        metafunc.parametrize("error", errors)  # type: ignore


def test_per_error(error: str):
    """Test that fails for each error found.
    If there are no errors, it will run once and pass.
    Works with pytest using indirect parametrization.
    (See pytest_generate_tests above)
    """
    assert error == NO_ERRORS


@media_file_parametrize
def test_mediafile_year_gt_zero(file: MediaFileData):
    assert file.year > 0, f"{file.path}"


@media_file_parametrize
def test_mediafile_years_lt_present(file: MediaFileData):
    assert file.year <= PRESENT_YEAR, f"{file.path}"


@media_file_parametrize
def test_mediafile_size_gt_min(file: MediaFileData):
    assert file.size >= MINIMUM_FILESIZE, f"{file.path}"


def genre_string_to_enum(s: str) -> Optional[Genre]:
    for genre in Genre:
        if genre.value == s:
            return genre
    return None


@media_file_parametrize
def test_mediafile_allowed_genres(file: MediaFileData):
    assert file.genre in get_all_genre_strings(), f"{file.path}"


@media_file_parametrize
def test_mediafile_libs_genres_mode_whitelist(file: MediaFileData):
    if LIB_GENRES_MODE_BLACKLIST:
        return
    for idx in range(LIB_COUNT):
        if file.path.find(LIBS_MEDIA_PATH[idx]) != -1:
            g = genre_string_to_enum(file.genre)
            assert (
                g is not None and g in LIBS_GENRES[idx]
            ), f"{file.path} (genre: {file.genre}) is not allowed by by LIB{idx + 1} LIBS_GENRES"


@media_file_parametrize
def test_mediafile_libs_genres_mode_blacklist(file: MediaFileData):
    if not LIB_GENRES_MODE_BLACKLIST:
        return
    for idx in range(LIB_COUNT):
        if file.path.find(LIBS_MEDIA_PATH[idx]) != -1:
            g = genre_string_to_enum(file.genre)
            assert (
                g is not None and g not in LIBS_GENRES[idx]
            ), f"{file.path} (genre: {file.genre}) is prohibited by LIB{idx + 1} LIBS_GENRES"


@media_file_parametrize
def test_mediafile_artist_is_not_empty(file: MediaFileData):
    assert len(file.artist) > 0, f"{file.path}"


@media_file_parametrize
def test_mediafile_albumartist_is_not_empty(file: MediaFileData):
    assert len(file.albumartist) > 0, f"{file.path}"


def test_mediafile_albumartist_same_for_every_track_in_every_album(
    files: list[MediaFileData],
):
    """
    Different tracks may have different artists e.g. "Dr. Dre feat. Snoop Dog"
    but all tracks in a an albums should have the same albumartist e.g. "Dr. Dre"
    """
    albums: dict[str, str] = {}
    for file in files:
        albumkey = f"{file.albumartist} - {file.album} [{file.year}]"
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
    files: list[MediaFileData],
):
    """
    Different tracks may have different artists e.g. "Dr. Dre feat. Snoop Dog"
    but all tracks under a given artist folder e.g. "Dr_ Dre" should have the same albumartist e.g. "Dr. Dre"
    and it should match the artist directory name (after escaping)
    """
    artists: dict[str, str] = {}
    for file in files:
        artist_dir_name = str(Path(file.path).parent.parent.name)
        albumartist_escaped = escape_artist_name(file.albumartist)
        if artist_dir_name in artists:
            assert (
                artists[artist_dir_name] == albumartist_escaped
            ), f"File (path={file.path}) albumartist '{file.albumartist}' (escaped={albumartist_escaped})  does not match artist directory name '{artist_dir_name}'"
        else:
            artists[artist_dir_name] = albumartist_escaped


def run_test_mediafile(tag_type: str, tag_type_2: Optional[str] = None) -> list[str]:
    """
    tag_type: the tag to test
    tag_type_2: optional secondary qualifier, makes it skip validation if tag_type_2
    doesn't match. E.g. tag_type="album" and tag_type_2="artist" => only compare
    two albums if the artist is the same for both of them.
    """
    errors: list[str] = []
    grouped: dict[str, list[MediaFileData]] = {}
    for file in load_yaml_media_files():
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
