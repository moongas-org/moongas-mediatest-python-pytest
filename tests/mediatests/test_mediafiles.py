import os
from pathlib import Path

from mediatest.config import get_config
from mediatest.path_utils import get_file_ext

"""
These tests validate media files by scanning the lib directories on the filesystem
"""

# TODO: Write test to disallow periods in filenames except as file extension separator
# TODO: Validate filenames, prohibited chars in filenames

# '’' is prohibited because it's problematic with ID3 tags (converts to '?' if ripped from CD),
# so I need to check the tags on these files and change '?' to ''' if needed.
# also disallow both regular question mark and weird unicode question mark
# >>> ord('?')
# 63
# >>> ord('？')
# 65311

FILENAME_PROHIBITED_CHARS = "’？?"


def get_mediafile_paths(media_lib_path: Path) -> list[Path]:
    ret: set[Path] = set()
    for root, _, files in os.walk(media_lib_path, topdown=False):
        for name in files:
            fullpath = Path(root) / name
            ret.add(fullpath)
    return list(ret)


def pytest_generate_tests(metafunc):  # type: ignore
    runtime_config = get_config()
    mediafile_paths: list[Path] = []
    for lib_idx in range(runtime_config.lib_count):
        media_lib_path = Path(runtime_config.libs_media_path[lib_idx])
        mediafile_paths.extend(get_mediafile_paths(media_lib_path))
    metafunc.parametrize("mediafile_path", mediafile_paths)  # type: ignore


def test_mediafile_filename(mediafile_path: Path):
    """Verifies that media file filename doesn't break any naming rules"""
    for c in FILENAME_PROHIBITED_CHARS:
        assert c not in mediafile_path.name


def test_mediafile_file_ext(mediafile_path: Path):
    """Verifies that media file file extension is in allowed_exts list"""
    ext = get_file_ext(mediafile_path)
    assert ext in get_config().allowed_exts, f"'{ext}' not in allowed extensions"
