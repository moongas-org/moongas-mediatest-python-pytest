import os
from pathlib import Path

from mediascan.utils.path.album_path import AlbumPathBuilder

from mediatest.config import EXTS_MEDIA, EXTS_METADATA, LIB_COUNT, LIBS_MEDIA_PATH
from mediatest.path_utils import get_path_depth, is_dir_with_files

"""
Filesystem tests that validate album directories
"""


def get_album_dir_paths(media_lib_path: Path) -> list[Path]:
    ret: set[Path] = set()
    base_depth = get_path_depth(media_lib_path)
    for root, dirs, _ in os.walk(media_lib_path, topdown=False):
        for name in dirs:
            fullpath = Path(root) / name
            current_depth = get_path_depth(fullpath)
            relative_depth = current_depth - base_depth
            # 1 = artist dir
            if relative_depth == 1:
                pass
            # 2 = album dir
            elif relative_depth == 2:
                ret.add(fullpath)
    return list(ret)


def pytest_generate_tests(metafunc):  # type: ignore
    album_dir_paths: list[Path] = []
    for lib_idx in range(LIB_COUNT):
        media_lib_path = Path(LIBS_MEDIA_PATH[lib_idx])
        album_dir_paths.extend(get_album_dir_paths(media_lib_path))
    metafunc.parametrize("album_path", album_dir_paths)  # type: ignore


def assert_is_dir_with_media_files(path: Path):
    """Asserts that album directory contains at least one media file
    and that directory does not contain subdirectories"""
    assert is_dir_with_files(path, EXTS_MEDIA)


def assert_is_dir_with_metadata_files(path: Path):
    """Asserts that album directory contains at least one metadata (.yml) file
    and that directory does not contain subdirectories"""
    assert is_dir_with_files(path, EXTS_METADATA)


def test_album_dir_name(album_path: Path):
    """Verifies that album directory name doesn't break any naming rules
    e.g. no '.' characters"""
    assert "." not in album_path.name
    album_path_obj = AlbumPathBuilder.of(album_path)
    assert album_path_obj.valid


def test_album_dir_contains_media_files(album_path: Path):
    """Verifies that album directory contains media files"""
    assert_is_dir_with_media_files(album_path)


def test_album_dir_contains_metadata_files(album_path: Path):
    """Verifies that album directory contains metadata (.yml) files"""
    assert_is_dir_with_metadata_files(album_path)


def test_album_cover_exists(album_path: Path):
    """
    That that verifies that cover.jpg file exists for the given album path
    """
    album_cover_file_path = Path(album_path) / "cover.jpg"
    assert album_cover_file_path.exists()
