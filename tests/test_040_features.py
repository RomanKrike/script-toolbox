# -*- coding: utf-8 -*-

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.executor import evaluate_python_state
from script_toolbox.model.items import create_item


def test_config_schema_is_16():
    assert CONFIG_VERSION == 16


def test_state_button_normalizes_state_fields():
    item = create_item(
        "button",
        {
            "label": "Visibility",
            "mode": "state",
            "state_get_script": "state = True",
            "state_on_script": "result = 'on'",
            "state_off_script": "result = 'off'",
        }
    )

    assert item["mode"] == "state"
    assert item["state_get_script"] == "state = True"
    assert item["state_on_script"] == "result = 'on'"
    assert item["state_off_script"] == "result = 'off'"
    assert item["state_on_label"] == "Visibility: ON"
    assert item["state_off_label"] == "Visibility: OFF"


def test_field_multiple_defaults_to_list_display():
    item = create_item(
        "field",
        {
            "multiple": True,
        }
    )

    assert item["multiple"] is True
    assert item["display_mode"] == "list"
    assert item["visible_rows"] == 4


def test_single_field_forces_single_line_and_single_value():
    item = create_item(
        "field",
        {
            "multiple": False,
            "display_mode": "list",
            "value": ["first", "second"],
        }
    )

    assert item["multiple"] is False
    assert item["display_mode"] == "single"
    assert item["value"] == "first"


def test_row_and_child_layout_settings_are_normalized():
    row = create_item(
        "row",
        {
            "spacing": 7,
            "equal_widths": True,
            "vertical_alignment": "bottom",
            "items": [
                {
                    "kind": "button",
                    "name": "stretch_button",
                    "row_width_mode": "stretch",
                    "row_stretch": 3,
                    "row_alignment": "right",
                },
                {
                    "kind": "button",
                    "name": "fixed_button",
                    "row_width_mode": "fixed",
                    "row_width": 160,
                },
            ],
        }
    )

    assert row["spacing"] == 7
    assert row["equal_widths"] is True
    assert row["vertical_alignment"] == "bottom"
    assert row["items"][0]["row_width_mode"] == "stretch"
    assert row["items"][0]["row_stretch"] == 3
    assert row["items"][0]["row_alignment"] == "right"
    assert row["items"][1]["row_width_mode"] == "fixed"
    assert row["items"][1]["row_width"] == 160


def test_value_controls_preserve_on_change_script():
    item = create_item(
        "integer",
        {
            "on_change_script": "result = value + 1",
        }
    )

    assert item["on_change_script"] == "result = value + 1"


def test_state_query_evaluator_reads_state_variable():
    assert evaluate_python_state(
        "state = True"
    ) is True
    assert evaluate_python_state(
        "state = False"
    ) is False
