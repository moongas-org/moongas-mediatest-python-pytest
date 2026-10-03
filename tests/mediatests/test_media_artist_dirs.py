import os
from pathlib import Path

from mediascan.artist_yaml_file_validator import validate_artist_yaml_file
from mediatest.config import LIB_COUNT, LIBS_MEDIA_PATH
from mediatest.path_utils import get_path_depth, is_dir_with_subdirs

"""
Filesystem tests that validate artist directories
"""

# TODO: Write test to find duplicated artists, e.g. "The Dave Matthews Band" vs "Dave Matthews Band"


def get_artist_dir_paths(media_lib_path: Path) -> list[Path]:
    ret: set[Path] = set()
    base_depth = get_path_depth(media_lib_path)
    for root, dirs, _ in os.walk(media_lib_path, topdown=False):
        for name in dirs:
            fullpath = Path(root) / name
            current_depth = get_path_depth(fullpath)
            relative_depth = current_depth - base_depth
            # 1 = artist dir
            if relative_depth == 1:
                ret.add(fullpath)
    return list(ret)


def pytest_generate_tests(metafunc):  # type: ignore
    artist_dir_paths: list[Path] = []
    for lib_idx in range(LIB_COUNT):
        media_lib_path = Path(LIBS_MEDIA_PATH[lib_idx])
        artist_dir_paths.extend(get_artist_dir_paths(media_lib_path))
    metafunc.parametrize("artist_path", artist_dir_paths)  # type: ignore


def test_artist_dir_name(artist_path: Path):
    """Verifies that artist directory name doesn't break any naming rules
    e.g. no '.' characters"""
    assert "." not in artist_path.name


def test_artist_dir_is_not_empty(artist_path: Path):
    """Verifies that artist directory contains subdirectories (albums)"""
    assert is_dir_with_subdirs(artist_path)


def test_artist_yaml_exists(artist_path: Path):
    """
    That that verifies that artist.yml file exists for the given artist path
    """
    artist_yaml_path = Path(artist_path) / "artist.yml"
    assert artist_yaml_path.exists()


def test_artist_yaml_is_valid(artist_path: Path):
    """
    Verifies that the artist.yml file is valid according to the schema
    """
    artist_yaml_path = Path(artist_path) / "artist.yml"
    artist_yaml_paths = [str(artist_yaml_path)]
    artists_missing: list[str] = []
    exceptions: list[tuple[Path, Exception]] = []
    validate_artist_yaml_file(
        artist_path.name,
        artist_path,
        artist_yaml_paths,
        artists_missing,
        exceptions,
    )
    assert not exceptions, "Artist YAML validation errors: " + "; ".join(
        f"{path}: {exception}" for path, exception in exceptions
    )
    assert not artists_missing, f"Artists missing artist.yml: {artists_missing}"
