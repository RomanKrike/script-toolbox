# -*- coding: utf-8 -*-

from script_toolbox.telemetry import events


def test_product_event_schema_accepts_reviewed_enum_properties():
    assert events.sanitize_product_event(
        "item_created",
        {
            "item_type": "Field",
        }
    ) == (
        "item_created",
        {
            "item_type": "field",
        }
    )

    assert events.sanitize_product_event(
        "config_imported",
        {
            "mode": "append",
        }
    ) == (
        "config_imported",
        {
            "mode": "append",
        }
    )


def test_product_event_schema_maps_future_item_types_to_other():
    assert events.sanitize_product_event(
        "item_activated",
        {
            "item_type": "future-widget",
        }
    ) == (
        "item_activated",
        {
            "item_type": "other",
        }
    )


def test_product_event_schema_rejects_unknown_events_and_properties():
    assert events.sanitize_product_event(
        "arbitrary_event",
        {}
    ) is None

    assert events.sanitize_product_event(
        "item_created",
        {
            "item_type": "field",
            "scene_path": "C:/secret/shot.ma",
        }
    ) is None

    assert events.sanitize_product_event(
        "config_imported",
        {
            "mode": "C:/secret/config.json",
        }
    ) is None


def test_track_product_event_only_forwards_sanitized_payload(monkeypatch):
    captured = []

    def fake_track(name, properties=None):
        captured.append(
            (name, properties)
        )
        return True

    monkeypatch.setattr(
        events.service,
        "track",
        fake_track
    )

    assert events.track_product_event(
        "share_created",
        {
            "share_type": "config",
        }
    ) is True
    assert captured == [
        (
            "share_created",
            {
                "share_type": "config",
            }
        )
    ]

    assert events.track_product_event(
        "share_created",
        {
            "share_type": "item",
            "label": "Private Tool Name",
        }
    ) is False
    assert len(captured) == 1
