# -*- coding: utf-8 -*-

import json

from script_toolbox.core import preferences


def test_missing_preferences_use_build_channel(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"

    monkeypatch.setattr(
        preferences,
        "BUILD_CHANNEL",
        "development"
    )

    assert preferences.get_update_channel(
        path=str(path)
    ) == "development"


def test_update_channel_round_trip(tmp_path):
    path = tmp_path / "settings.json"

    assert preferences.set_update_channel(
        "development",
        path=str(path)
    ) == "development"

    assert preferences.get_update_channel(
        path=str(path)
    ) == "development"

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )
    assert data["update_channel"] == "development"


def test_invalid_update_channel_falls_back_to_stable(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        '{"update_channel": "nightly"}',
        encoding="utf-8"
    )

    assert preferences.get_update_channel(
        path=str(path)
    ) == "stable"
