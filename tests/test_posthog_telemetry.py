# -*- coding: utf-8 -*-

import json

import pytest

from script_toolbox import telemetry
from script_toolbox.telemetry import posthog_provider
from script_toolbox.telemetry import runtime


class FakeResponse(object):
    def __init__(self, status=200):
        self.status = status
        self.closed = False

    def getcode(self):
        return self.status

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def reset_telemetry_service():
    from script_toolbox.telemetry import service

    service.reset()
    runtime._START_EVENT_SENT = False
    yield
    service.reset()
    runtime._START_EVENT_SENT = False


def test_posthog_capture_forces_anonymous_session_properties(monkeypatch):
    provider = telemetry.PostHogProvider(
        "phc_test",
        "https://eu.i.posthog.com",
        distinct_id="stb-session-test",
    )
    captured = []

    monkeypatch.setattr(
        provider,
        "_send_event",
        lambda event: captured.append(event) or True,
    )

    assert provider.capture(
        "plugin_started",
        {
            "plugin_version": "1.2.3",
            "distinct_id": "must-not-win",
            "$process_person_profile": True,
        },
    ) is True
    assert provider.flush() is True

    assert captured == [
        {
            "event": "plugin_started",
            "properties": {
                "plugin_version": "1.2.3",
                "distinct_id": "stb-session-test",
                "$process_person_profile": False,
                "$lib": "script-toolbox",
                "$lib_version": posthog_provider.PLUGIN_VERSION,
            },
        }
    ]


def test_posthog_provider_posts_to_batch_endpoint(monkeypatch):
    requests = []
    response = FakeResponse()

    def fake_urlopen(request, timeout=None):
        requests.append((request, timeout))
        return response

    monkeypatch.setattr(
        posthog_provider,
        "urlopen",
        fake_urlopen,
    )

    provider = telemetry.PostHogProvider(
        "phc_test",
        "https://eu.i.posthog.com/",
        timeout=4,
        distinct_id="stb-session-test",
    )

    event = {
        "event": "plugin_started",
        "properties": {
            "distinct_id": "stb-session-test",
            "$process_person_profile": False,
        },
    }

    assert provider._send_event(event) is True
    assert len(requests) == 1

    request, timeout = requests[0]
    assert request.get_full_url() == "https://eu.i.posthog.com/batch/"
    assert timeout == 4

    payload = json.loads(request.data.decode("utf-8"))
    assert payload["api_key"] == "phc_test"
    assert payload["batch"] == [event]
    assert "sent_at" in payload
    assert response.closed is True


def test_default_runtime_never_enables_without_explicit_consent(monkeypatch):
    monkeypatch.setattr(
        runtime,
        "POSTHOG_PROJECT_TOKEN",
        "phc_test",
    )
    monkeypatch.setattr(
        runtime,
        "POSTHOG_HOST",
        "https://eu.i.posthog.com",
    )
    monkeypatch.setattr(
        runtime,
        "get_telemetry_consent",
        lambda: None,
    )

    status = runtime.configure_default_telemetry()

    assert status["provider"] == "posthog"
    assert status["enabled"] is False
    assert telemetry.track("plugin_started") is False


def test_default_runtime_enables_only_for_true_consent(monkeypatch):
    monkeypatch.setattr(
        runtime,
        "POSTHOG_PROJECT_TOKEN",
        "phc_test",
    )
    monkeypatch.setattr(
        runtime,
        "POSTHOG_HOST",
        "https://eu.i.posthog.com",
    )
    monkeypatch.setattr(
        runtime,
        "get_telemetry_consent",
        lambda: True,
    )

    status = runtime.configure_default_telemetry()

    assert status["provider"] == "posthog"
    assert status["enabled"] is True


def test_missing_build_token_falls_back_to_null_provider(monkeypatch):
    monkeypatch.setattr(
        runtime,
        "POSTHOG_PROJECT_TOKEN",
        "",
    )
    monkeypatch.setattr(
        runtime,
        "get_telemetry_consent",
        lambda: True,
    )

    status = runtime.configure_default_telemetry()

    assert status["provider"] == "none"
    assert status["enabled"] is False


def test_common_properties_are_limited_to_reviewed_technical_metadata():
    properties = runtime.default_common_properties()

    assert set(properties) == {
        "plugin_version",
        "build_channel",
        "build_number",
        "host",
        "host_version",
        "os",
    }
