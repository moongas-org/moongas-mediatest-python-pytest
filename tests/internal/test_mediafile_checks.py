import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    ("filename", "failed_test"),
    [
        ("Song.mp3", None),
        ("cover.jpg", None),
        ("Song?.mp3", "test_mediafile_filename"),
        ("Song.invalid", "test_mediafile_file_ext"),
    ],
)
def test_filesystem_mediafile_tests(
    tmp_path: Path, filename: str, failed_test: str | None
) -> None:
    (tmp_path / "mediatest-config.yml").write_text(
        "minimumFilesize: 123\n", encoding="utf-8"
    )
    (tmp_path / "mediascan-config.yml").write_text(
        "mediaDirs: [Music]\nmediaExts: [.mp3]\n", encoding="utf-8"
    )
    album_path = tmp_path / "Music/Artist/Album"
    album_path.mkdir(parents=True)
    (album_path / filename).write_bytes(b"x" * 123)
    test_path = Path(__file__).resolve().parents[1] / "mediatests/test_mediafiles.py"
    source_path = str(test_path.parents[2] / "src")
    pythonpath = os.pathsep.join(filter(None, (source_path, os.environ.get("PYTHONPATH"))))
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from pathlib import Path; import pytest; "
            "from mediatest.config import configure; configure(Path(sys.argv[1])); "
            "sys.exit(pytest.main([sys.argv[2], '-o', 'addopts=', '-q']))",
            str(tmp_path),
            str(test_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": pythonpath},
    )
    output = result.stdout + result.stderr
    if failed_test is None:
        assert result.returncode == 0, output
        assert "2 passed" in output
    else:
        assert result.returncode == 1, output
        assert failed_test in output
        assert "1 failed, 1 passed" in output
