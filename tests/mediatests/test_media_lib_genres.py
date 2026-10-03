from typing import Set

import pytest

from mediatest.config import LIB_COUNT, LIBS_GENRES
from mediatest.media_utils import get_all_genre_strings

"""
These tests only test the mediatest configuration itself,
e.g. whether the Genres lists under each lib defintion are valid.
"""


@pytest.mark.parametrize("lib_idx", list(range(LIB_COUNT)))
def test_lib_genres_no_dupes(lib_idx: int):
    s: Set[str] = set()
    for genre in LIBS_GENRES[lib_idx]:
        if genre in s:
            pytest.exit(f"Duplicate genre detected in LIB{lib_idx}_GENRES: {genre}")
        s.add(genre)


def test_lib_genres_no_intersections():
    """TODO: Make this work for more than two libs"""
    for idx in range(LIB_COUNT):
        if idx == LIB_COUNT - 1:
            return
        intersection = set(LIBS_GENRES[idx]) & set(LIBS_GENRES[idx + 1])
        if len(intersection):
            pytest.exit(f"Duplicate genres in both LIB{idx + 1} and LIB{idx + 2}: {str(intersection)}")


def test_lib_genres_all_genres_used():
    for genre in get_all_genre_strings():
        found = False
        for i in range(LIB_COUNT):
            if genre in LIBS_GENRES[i]:
                found = True
                break
        if not found:
            pytest.exit(f"Genre '{genre}' not in any lib genres whitelist. Did you forget to add it to test config?")
