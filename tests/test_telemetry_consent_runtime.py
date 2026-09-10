# -*- coding: utf-8 -*-

from script_toolbox.telemetry import runtime


def test_apply_consent_true_persists_and_initializes(monkeypatch):
    persisted = []

    monkeypatch.setattr(
        runtime,
        "set_telemetry_consent",
        lambda value: persisted.append(value) or True,
    )
    monkeypatch.setattr(
        runtime,
        "initialize_telemetry",
        lambda: {"enabled": True, "provider": "posthog"},
    )

    def unexpected_refresh():
        raise AssertionError("refresh should not be used for opt-in")

    monkeypatch.setattr(
        runtime,
        "refresh_telemetry",
        unexpected_refresh,
    )

    status = runtime.apply_telemetry_consent(True)

    assert persisted == [True]
    assert status["enabled"] is True
    assert status["provider"] == "posthog"


def test_apply_consent_false_persists_and_refreshes(monkeypatch):
    persisted = []

    monkeypatch.setattr(
        runtime,
        "set_telemetry_consent",
        lambda value: persisted.append(value) or False,
    )
    monkeypatch.setattr(
        runtime,
        "refresh_telemetry",
        lambda: {"enabled": False, "provider": "posthog"},
    )

    def unexpected_initialize():
        raise AssertionError("initialize should not be used for opt-out")

    monkeypatch.setattr(
        runtime,
        "initialize_telemetry",
        unexpected_initialize,
    )

    status = runtime.apply_telemetry_consent(False)

    assert persisted == [False]
    assert status["enabled"] is False


def test_apply_consent_none_preserves_undecided_state(monkeypatch):
    persisted = []

    monkeypatch.setattr(
        runtime,
        "set_telemetry_consent",
        lambda value: persisted.append(value) or None,
    )
    monkeypatch.setattr(
        runtime,
        "refresh_telemetry",
        lambda: {"enabled": False, "provider": "posthog"},
    )

    status = runtime.apply_telemetry_consent(None)

    assert persisted == [None]
    assert status["enabled"] is False
