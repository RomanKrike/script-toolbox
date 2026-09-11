# -*- coding: utf-8 -*-

import pytest

from script_toolbox import telemetry


class RecordingProvider(telemetry.TelemetryProvider):
    name = "recording"

    def __init__(self):
        self.events = []

    def capture(self, event_name, properties=None):
        self.events.append((event_name, dict(properties or {})))
        return True


class FailingProvider(telemetry.TelemetryProvider):
    name = "failing"

    def capture(self, event_name, properties=None):
        raise RuntimeError("network unavailable")


@pytest.fixture(autouse=True)
def reset_telemetry_service():
    from script_toolbox.telemetry import service

    service.reset()
    yield
    service.reset()


def test_telemetry_is_disabled_and_null_by_default():
    assert telemetry.is_enabled() is False
    assert telemetry.active_provider_name() == "none"
    assert telemetry.track("plugin_started") is False


def test_registered_provider_can_be_selected_without_business_logic_change():
    provider = RecordingProvider()
    telemetry.register_provider(provider)
    telemetry.configure(
        provider_name="recording",
        enabled=True,
        common_properties={
            "plugin_version": "1.2.3",
            "host": "maya",
        },
    )

    assert telemetry.track(
        "item_created",
        {"item_type": "field"},
    ) is True
    assert provider.events == [
        (
            "item_created",
            {
                "plugin_version": "1.2.3",
                "host": "maya",
                "item_type": "field",
            },
        )
    ]


def test_provider_can_be_switched_at_runtime():
    first = RecordingProvider()
    first.name = "first"
    second = RecordingProvider()
    second.name = "second"

    telemetry.register_provider(first)
    telemetry.register_provider(second)
    telemetry.configure("first", enabled=True)
    telemetry.track("event_one")

    telemetry.set_provider("second")
    telemetry.track("event_two")

    assert [event[0] for event in first.events] == ["event_one"]
    assert [event[0] for event in second.events] == ["event_two"]


def test_disabled_telemetry_never_calls_provider():
    provider = RecordingProvider()
    telemetry.register_provider(provider)
    telemetry.configure("recording", enabled=False)

    assert telemetry.track("plugin_started") is False
    assert provider.events == []


def test_provider_failure_never_breaks_plugin_execution():
    telemetry.register_provider(FailingProvider())
    telemetry.configure("failing", enabled=True)

    assert telemetry.track("plugin_started") is False


def test_duplicate_provider_requires_explicit_replace():
    telemetry.register_provider(RecordingProvider())

    with pytest.raises(telemetry.TelemetryError):
        telemetry.register_provider(RecordingProvider())
