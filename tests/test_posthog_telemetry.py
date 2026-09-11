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


class FakeUuid(object):
    hex = "0123456789abcdef0123456789abcdef"


@pytest.fixture(autouse=True)
def reset_telemetry_service():
    from script_toolbox.telemetry import service

    service.reset()
    runtime._START_EVENT_SENT = False
    yield
    service.reset()
    runtime._START_EVENT_SENT = False


def test_posthog_capture_forces_provider_owned_identity_properties(monkeypatch):
    provider = telemetry.PostHogProvider(
        "phc_test",
        "https://eu.i.posthog.com",
        distinct_id="stb-install-test",
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
                "distinct_id": "stb-install-test",
                "$process_person_profile": False,
                "$lib": "script-toolbox",
                "$lib_version": posthog_provider.PLUGIN_VERSION,
            },
        }
    ]

    assert provider.close() is True
    assert provider.flush() is True


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
        distinct_id="stb-install-test",
    )

    event = {
        "event": "plugin_started",
        "properties": {
            "distinct_id": "stb-install-test",
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


def test_default_runtime_never_creates_identity_without_explicit_consent(monkeypatch):
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

    def unexpected_get_installation_id():
        raise AssertionError("installation id must not be read before opt-in")

    monkeypatch.setattr(
        runtime,
        "get_telemetry_installation_id",
        unexpected_get_installation_id,
    )

    status = runtime.configure_default_telemetry()

    assert status["provider"] == "posthog"
    assert status["enabled"] is False
    assert telemetry.track("plugin_started") is False


def test_default_runtime_reuses_persisted_installation_id(monkeypatch):
    installation_id = "stb-install-0123456789abcdef0123456789abcdef"
    captured = []

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
    monkeypatch.setattr(
        runtime,
        "get_telemetry_installation_id",
        lambda: installation_id,
    )
    monkeypatch.setattr(
        runtime,
        "track_product_event",
        lambda name, properties=None: captured.append(name) or True,
    )

    status = runtime.configure_default_telemetry()
    provider = telemetry.get_provider("posthog")

    assert status["provider"] == "posthog"
    assert status["enabled"] is True
    assert provider.distinct_id == installation_id
    assert captured == []


def test_default_runtime_creates_installation_id_after_opt_in(monkeypatch):
    persisted = []
    captured = []

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
    monkeypatch.setattr(
        runtime,
        "get_telemetry_installation_id",
        lambda: None,
    )
    monkeypatch.setattr(
        runtime.uuid,
        "uuid4",
        lambda: FakeUuid(),
    )
    monkeypatch.setattr(
        runtime,
        "set_telemetry_installation_id",
        lambda value: persisted.append(value) or value,
    )
    monkeypatch.setattr(
        runtime,
        "track_product_event",
        lambda name, properties=None: captured.append(name) or True,
    )

    status = runtime.configure_default_telemetry()
    provider = telemetry.get_provider("posthog")

    expected = "stb-install-0123456789abcdef0123456789abcdef"
    assert persisted == [expected]
    assert status["enabled"] is True
    assert provider.distinct_id == expected
    assert captured == ["installation_created"]


def test_missing_build_token_falls_back_without_creating_identity(monkeypatch):
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

    def unexpected_get_installation_id():
        raise AssertionError("identity must not be created without transport")

    monkeypatch.setattr(
        runtime,
        "get_telemetry_installation_id",
        unexpected_get_installation_id,
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
