# -*- coding: utf-8 -*-

import io
import json
import os
import warnings

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core import config


def _config_path(tmp_path):
    return str(
        tmp_path /
        "toolbox.json"
    )


def test_load_config_missing_file_returns_default(tmp_path):
    document = config.load_config(
        path=_config_path(tmp_path)
    )

    assert document["version"] == CONFIG_VERSION
    assert document["sections"]


def test_save_then_load_round_trip(tmp_path):
    path = _config_path(tmp_path)

    original = config.load_config(path=path)
    original["sections"][0]["name"] = "Renamed"

    written_path = config.save_config(
        original,
        path=path
    )

    assert written_path == path
    assert os.path.isfile(path)

    reloaded = config.load_config(path=path)
    assert reloaded["sections"][0]["name"] == "Renamed"


def test_save_config_creates_missing_parent_directory(tmp_path):
    path = str(
        tmp_path /
        "nested" /
        "deeper" /
        "toolbox.json"
    )

    config.save_config(
        {},
        path=path
    )

    assert os.path.isfile(path)


def test_save_config_leaves_no_temp_file_behind(tmp_path):
    path = _config_path(tmp_path)

    config.save_config(
        {},
        path=path
    )

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

    with io.open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:
        original_text = handle.read()

    def _boom(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(
        json,
        "dumps",
        _boom
    )

    with pytest.raises(RuntimeError):
        config.save_config({}, path=path)

    with io.open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:
        assert handle.read() == original_text


def test_save_config_preserves_original_on_replace_failure(
    tmp_path,
    monkeypatch
):
    path = _config_path(tmp_path)
    config.save_config({}, path=path)

    with io.open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:
        original_text = handle.read()

    def _boom(source, destination):
        raise OSError("replace failed")

    monkeypatch.setattr(
        config,
        "_replace_file",
        _boom
    )

    with pytest.raises(OSError):
        config.save_config({}, path=path)

    with io.open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:
        assert handle.read() == original_text

    assert sorted(os.listdir(str(tmp_path))) == [
        os.path.basename(path)
    ]


def test_python2_windows_replace_path_never_removes_target(monkeypatch):
    calls = []

    monkeypatch.setattr(
        config.os,
        "replace",
        None
    )
    monkeypatch.setattr(
        config.os,
        "name",
        "nt"
    )
    monkeypatch.setattr(
        config,
        "_replace_file_windows",
        lambda source, destination: calls.append(
            (source, destination)
        )
    )
    monkeypatch.setattr(
        config.os,
        "remove",
        lambda *args: pytest.fail(
            "Windows replacement must not delete the destination first"
        )
    )

    config._replace_file(
        "source.tmp",
        "toolbox.json"
    )

    assert calls == [
        ("source.tmp", "toolbox.json")
    ]


def test_load_config_warns_and_falls_back_on_corrupt_file(tmp_path):
    path = _config_path(tmp_path)

    with io.open(
        path,
        "w",
        encoding="utf-8"
    ) as handle:
        handle.write(u"{not valid json")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        document = config.load_config(path=path)

    assert document["version"] == CONFIG_VERSION
    assert document["sections"]
    assert any(
        "failed to load config" in str(item.message)
        for item in caught
    )


def test_export_import_round_trip(tmp_path):
    path = _config_path(tmp_path)

    config.export_config(
        {
            "sections": [
                {
                    "kind": "folder",
                    "name": "Exported",
                }
            ],
        },
        path
    )

    document = config.import_config(path)
    assert document["sections"][0]["name"] == "Exported"
