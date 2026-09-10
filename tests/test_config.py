# -*- coding: utf-8 -*-

import io
import json
import os
import warnings

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core import config


def _config_path(tmp_path):
    return str(tmp_path / "toolbox.json")


def _document(name):
    return {
        "version": CONFIG_VERSION,
        "sections": [
            {
                "kind": "folder",
                "name": name,
                "label": name,
                "items": [],
            }
        ],
    }


def _read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def test_load_config_missing_file_returns_current_default(tmp_path):
    document = config.load_config(path=_config_path(tmp_path))

    assert document["version"] == CONFIG_VERSION
    assert document["sections"]


def test_save_then_load_round_trip(tmp_path):
    path = _config_path(tmp_path)
    original = config.load_config(path=path)
    original["sections"][0]["name"] = "Renamed"

    assert config.save_config(original, path=path) == path
    assert config.load_config(path=path)["sections"][0]["name"] == "Renamed"


def test_save_config_creates_missing_parent_directory(tmp_path):
    path = str(tmp_path / "nested" / "deeper" / "toolbox.json")

    config.save_config({}, path=path)

    assert os.path.isfile(path)


def test_first_save_creates_no_backup(tmp_path):
    path = _config_path(tmp_path)

    config.save_config(_document("First"), path=path)

    assert os.path.isfile(path)
    assert config.valid_backup_paths(path) == []


def test_save_config_rotates_three_previous_valid_versions(tmp_path):
    path = _config_path(tmp_path)

    for name in ("One", "Two", "Three", "Four"):
        config.save_config(_document(name), path=path)

    assert config.load_config(path)["sections"][0]["name"] == "Four"
    assert config.load_config(
        config.backup_path(path, 1)
    )["sections"][0]["name"] == "Three"
    assert config.load_config(
        config.backup_path(path, 2)
    )["sections"][0]["name"] == "Two"
    assert config.load_config(
        config.backup_path(path, 3)
    )["sections"][0]["name"] == "One"
    assert not os.path.exists(config.backup_path(path, 4))


def test_save_config_leaves_no_temp_file_behind(tmp_path):
    path = _config_path(tmp_path)

    config.save_config({}, path=path)

    leftovers = [
        name
        for name in os.listdir(str(tmp_path))
        if name != os.path.basename(path)
    ]
    assert leftovers == []


def test_save_config_does_not_destroy_original_on_write_failure(
    tmp_path,
    monkeypatch
):
    path = _config_path(tmp_path)
    config.save_config({}, path=path)
    original_text = _read_text(path)

    def _boom(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(json, "dumps", _boom)

    with pytest.raises(RuntimeError):
        config.save_config({}, path=path)

    assert _read_text(path) == original_text
    assert config.valid_backup_paths(path) == []


def test_save_config_preserves_original_on_replace_failure(
    tmp_path,
    monkeypatch
):
    path = _config_path(tmp_path)
    config.save_config(_document("Original"), path=path)
    original_text = _read_text(path)

    def _boom(source, destination):
        raise OSError("replace failed")

    monkeypatch.setattr(config, "_replace_file", _boom)

    with pytest.raises(OSError):
        config.save_config(_document("Replacement"), path=path)

    assert _read_text(path) == original_text
    assert _read_text(config.backup_path(path, 1)) == original_text


def test_save_refuses_to_overwrite_corrupt_primary(tmp_path):
    path = _config_path(tmp_path)
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(u"{broken")

    original_text = _read_text(path)

    with pytest.raises(config.ConfigRecoveryRequired):
        config.save_config(_document("Replacement"), path=path)

    assert _read_text(path) == original_text
    assert config.valid_backup_paths(path) == []


def test_python2_windows_replace_path_never_removes_target(monkeypatch):
    calls = []

    monkeypatch.setattr(config.os, "replace", None)
    monkeypatch.setattr(config.os, "name", "nt")
    monkeypatch.setattr(
        config,
        "_replace_file_windows",
        lambda source, destination: calls.append((source, destination))
    )
    monkeypatch.setattr(
        config.os,
        "remove",
        lambda *args: pytest.fail(
            "Windows replacement must not delete the destination first"
        )
    )

    config._replace_file("source.tmp", "toolbox.json")

    assert calls == [("source.tmp", "toolbox.json")]


def test_load_corrupt_config_without_backup_requires_recovery(tmp_path):
    path = _config_path(tmp_path)
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(u"{not valid json")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(config.ConfigRecoveryRequired) as error:
            config.load_config(path=path)

    assert error.value.path == path
    assert error.value.backups == []
    assert _read_text(path) == u"{not valid json"
    assert any("recovery is required" in str(item.message) for item in caught)


def test_load_corrupt_config_recovers_latest_valid_backup(tmp_path):
    path = _config_path(tmp_path)
    config.save_config(_document("One"), path=path)
    config.save_config(_document("Two"), path=path)

    damaged_text = u"{damaged primary"
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(damaged_text)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        recovered = config.load_config(path=path)

    assert recovered["sections"][0]["name"] == "One"
    assert config.load_config(path)["sections"][0]["name"] == "One"
    assert _read_text(path + ".corrupt") == damaged_text
    assert any("Recovered automatically" in str(item.message) for item in caught)


def test_recovery_skips_invalid_newest_backup(tmp_path):
    path = _config_path(tmp_path)
    config.save_config(_document("One"), path=path)
    config.save_config(_document("Two"), path=path)
    config.save_config(_document("Three"), path=path)

    with io.open(
        config.backup_path(path, 1),
        "w",
        encoding="utf-8"
    ) as handle:
        handle.write(u"{bad backup")
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(u"{bad primary")

    recovered = config.load_config(path=path)
    assert recovered["sections"][0]["name"] == "One"


def test_restore_config_backup_preserves_damaged_primary(tmp_path):
    path = _config_path(tmp_path)
    config.save_config(_document("Safe"), path=path)
    config.save_config(_document("Current"), path=path)

    damaged_text = u"broken primary"
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(damaged_text)

    result = config.restore_config_backup(path)

    assert result["document"]["sections"][0]["name"] == "Safe"
    assert result["corrupt_copy"] == path + ".corrupt"
    assert _read_text(path + ".corrupt") == damaged_text


def test_export_import_round_trip_requires_current_schema(tmp_path):
    path = _config_path(tmp_path)

    config.export_config(_document("Exported"), path)

    document = config.import_config(path)
    assert document["version"] == CONFIG_VERSION
    assert document["sections"][0]["name"] == "Exported"
