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


def test_installation_created_accepts_no_event_specific_properties():
    assert events.sanitize_product_event(
        "installation_created",
        {}
    ) == (
        "installation_created",
        {}
    )

    assert events.sanitize_product_event(
        "installation_created",
        {
            "installation_id": "must-not-be-a-property",
        }
    ) is None


def test_product_event_schema_maps_future_item_types_to_other():
    assert events.sanitize_product_event(
        "item_created",
        {
            "item_type": "future-widget",
        }
    ) == (
        "item_created",
        {
            "item_type": "other",
        }
    )


def test_noisy_ui_events_are_not_part_of_public_catalog():
    for event_name in (
        "editor_opened",
        "settings_opened",
        "item_activated",
    ):
        assert events.sanitize_product_event(
            event_name,
            {}
        ) is None


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
