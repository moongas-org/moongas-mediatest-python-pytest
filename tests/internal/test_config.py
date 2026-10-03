import logging
import shutil
from pathlib import Path

import pytest

from mediatest import config as config_module
from mediatest.config import MediaTestConfigUtil


def test_main_uses_live_config_state_after_configure():
    import mediatest.main as main_module

    source_config_path = Path(__file__).resolve().parents[2] / "mediatest-config.yml"
    config_module.configure(source_config_path)

    assert main_module.config.MEDIATEST_ROOTDIR == config_module.CONFIG.mediatest_rootdir
    assert main_module.config.MEDIATEST_ROOTDIR == config_module.MEDIATEST_ROOTDIR


def test_load_config_logs_config_source(caplog: pytest.LogCaptureFixture, tmp_path: Path):
    caplog.set_level(logging.DEBUG)
    source_config_path = Path(__file__).resolve().parents[2] / "mediatest-config.yml"
    config_directory = tmp_path / "config"
    config_directory.mkdir()
    config_path = config_directory / source_config_path.name
    shutil.copy(source_config_path, config_path)

    config = MediaTestConfigUtil().load_config(config_path)

    assert config is not None
    assert "Attempting to load config from" in caplog.text
    assert "Loaded config from" in caplog.text


def test_load_config_from_path(tmp_path: Path):
    source_config_path = Path(__file__).resolve().parents[2] / "mediatest-config.yml"
    config_directory = tmp_path / "config"
    config_directory.mkdir()
    config_path = config_directory / source_config_path.name
    shutil.copy(source_config_path, config_path)

    config = MediaTestConfigUtil().load_config(config_path)

    assert len(config.libs) == 2
    assert config.libs[0].media_path == "/data/Music/"
    assert config.libs[0].expected_media_count == 21666
    assert config.libs[1].media_path == "/data/MusicOther/"
    assert config.libs[1].expected_media_count == 0