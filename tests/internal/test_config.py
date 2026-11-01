import logging
import shutil
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from mediatest import config as config_module
from mediatest.config import MediaTestConfigUtil


def write_collection_configs(collection_rootdir: Path) -> None:
    (collection_rootdir / "mediatest-config.yml").write_text(
        "minimumFilesize: 123\n"
        "logThrottleSeconds: 0.5\n",
        encoding="utf-8",
    )
    (collection_rootdir / "mediascan-config.yml").write_text(
        "mediaDirs:\n"
        "  - Music\n"
        "  - /absolute/MusicOther\n"
        "mediaExts:\n"
        "  - .mp3\n"
        "  - .m4a\n",
        encoding="utf-8",
    )


def test_main_uses_live_config_state_after_configure(tmp_path: Path):
    import mediatest.main as main_module

    write_collection_configs(tmp_path)
    runtime_config = config_module.configure(tmp_path)

    assert runtime_config.mediatest_rootdir == str(
        tmp_path / "moongas-mediatest-python-pytest"
    )
    assert main_module.config.get_config() is runtime_config
    assert runtime_config.libs_media_path == (
        str((tmp_path / "Music").resolve()),
        str(Path("/absolute/MusicOther")),
    )
    assert runtime_config.exts_media == ("mp3", "m4a")
    assert runtime_config.exts_art == ("jpg", "webp", "png", "xcf")
    assert runtime_config.exts_lyrics == ("lrc", "txt")
    assert runtime_config.exts_metadata == ("yml",)
    assert runtime_config.exts_extra == ("pdf",)
    assert runtime_config.allowed_exts == (
        "mp3",
        "m4a",
        "jpg",
        "webp",
        "png",
        "xcf",
        "lrc",
        "txt",
        "yml",
        "pdf",
    )
    assert runtime_config.mediascan_db_path == str(
        (tmp_path / "mediascan.db").resolve()
    )
    assert runtime_config.minimum_filesize == 123
    assert runtime_config.log_throttle_seconds == 0.5


def test_config_is_immutable(tmp_path: Path):
    write_collection_configs(tmp_path)
    runtime_config = config_module.configure(tmp_path)

    with pytest.raises(FrozenInstanceError):
        setattr(runtime_config, "minimum_filesize", 456)
    with pytest.raises(FrozenInstanceError):
        setattr(runtime_config.media_test_config, "minimum_filesize", 456)
    with pytest.raises(TypeError):
        runtime_config.exts_media[0] = "flac"  # type: ignore[index]


@pytest.mark.parametrize("use_environment", [True, False])
@pytest.mark.parametrize("root_setting", [None, "custom-mediatest", "absolute"])
def test_main_resolves_mediatest_rootdir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    use_environment: bool,
    root_setting: str | None,
):
    import mediatest.main as main_module

    write_collection_configs(tmp_path)
    expected_root = tmp_path / "moongas-mediatest-python-pytest"
    if root_setting is not None:
        configured_root = (
            str(tmp_path / "absolute-mediatest")
            if root_setting == "absolute"
            else root_setting
        )
        with (tmp_path / "mediatest-config.yml").open(
            "a", encoding="utf-8"
        ) as config_file:
            config_file.write(f"mediatestRootdir: {configured_root}\n")
        expected_root = (tmp_path / configured_root).resolve()
    if use_environment:
        monkeypatch.setattr("sys.argv", ["mediatest"])
        monkeypatch.setenv("MOONGAS_COLLECTION_ROOTDIR", str(tmp_path))
    else:
        monkeypatch.setattr("sys.argv", ["mediatest", str(tmp_path)])
        monkeypatch.delenv("MOONGAS_COLLECTION_ROOTDIR", raising=False)
    pytest_args: list[str] = []

    def fake_pytest_main(args: list[str], plugins: list[object]) -> pytest.ExitCode:
        pytest_args.extend(args)
        return pytest.ExitCode.OK

    monkeypatch.setattr(main_module.pytest, "main", fake_pytest_main)

    with pytest.raises(SystemExit) as exit_info:
        main_module.main()

    assert exit_info.value.code == 0
    assert pytest_args[0] == str(expected_root / "tests" / "mediatests")
    rootdir_option = pytest_args.index("--rootdir")
    assert pytest_args[rootdir_option + 1] == str(expected_root)


def test_main_requires_collection_rootdir_without_environment(
    monkeypatch: pytest.MonkeyPatch,
):
    import mediatest.main as main_module

    monkeypatch.setattr("sys.argv", ["mediatest"])
    monkeypatch.delenv("MOONGAS_COLLECTION_ROOTDIR", raising=False)

    with pytest.raises(SystemExit) as exit_info:
        main_module.main()

    assert exit_info.value.code == 2


def test_load_config_logs_config_source(caplog: pytest.LogCaptureFixture, tmp_path: Path):
    caplog.set_level(logging.DEBUG)
    source_config_path = Path(__file__).resolve().parents[2] / "mediatest-config.yml"
    config_directory = tmp_path / "config"
    config_directory.mkdir()
    config_path = config_directory / source_config_path.name
    shutil.copy(source_config_path, config_path)

    config = MediaTestConfigUtil().load_config(config_path)

    assert config is not None
    assert "Attempting to load mediatest config from" in caplog.text
    assert "Loaded mediatest config from" in caplog.text


def test_load_config_from_path(tmp_path: Path):
    source_config_path = Path(__file__).resolve().parents[2] / "mediatest-config.yml"
    config_directory = tmp_path / "config"
    config_directory.mkdir()
    config_path = config_directory / source_config_path.name
    shutil.copy(source_config_path, config_path)

    config = MediaTestConfigUtil().load_config(config_path)

    assert config.minimum_filesize == 10000