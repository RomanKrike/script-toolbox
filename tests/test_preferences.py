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


def test_telemetry_consent_is_unknown_until_user_decides(tmp_path):
    path = tmp_path / "settings.json"

    assert preferences.get_telemetry_consent(
        path=str(path)
    ) is None


def test_telemetry_consent_round_trip(tmp_path):
    path = tmp_path / "settings.json"

    assert preferences.set_telemetry_consent(
        True,
        path=str(path)
    ) is True
    assert preferences.get_telemetry_consent(
        path=str(path)
    ) is True

    assert preferences.set_telemetry_consent(
        False,
        path=str(path)
    ) is False
    assert preferences.get_telemetry_consent(
        path=str(path)
    ) is False

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["telemetry_consent"] is False


def test_invalid_telemetry_consent_is_treated_as_undecided(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        '{"telemetry_consent": "maybe"}',
        encoding="utf-8"
    )

    assert preferences.get_telemetry_consent(
        path=str(path)
    ) is None


def test_inspector_section_state_round_trip_is_editor_preference(tmp_path):
    path = tmp_path / "settings.json"

    assert preferences.get_inspector_section_collapsed(
        "appearance",
        path=str(path)
    ) is False
    assert preferences.set_inspector_section_collapsed(
        "appearance",
        True,
        path=str(path)
    ) is True
    assert preferences.get_inspector_section_collapsed(
        "appearance",
        path=str(path)
    ) is True

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["inspector_sections"]["appearance"] is True
    assert "config_version" not in data
