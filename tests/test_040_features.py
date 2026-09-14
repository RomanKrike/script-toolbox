# -*- coding: utf-8 -*-

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.executor import evaluate_python_state
from script_toolbox.model.bindings import matching_bindings
from script_toolbox.model.items import create_item


def test_config_schema_is_21():
    assert CONFIG_VERSION == 21


def test_toggle_button_normalizes_state_fields_and_default_trigger():
    item = create_item(
        "toggle_button",
        {
            "ui": {"label": "Visibility"},
            "props": {
                "state_source": "script",
                "state_get_script": "state = True",
                "state_on_script": "result = 'on'",
                "state_off_script": "result = 'off'",
            },
        }
    )

    props = item["props"]
    assert item["kind"] == "toggle_button"
    assert props["state_source"] == "script"
    assert "value" not in props
    assert props["state_get_script"] == "state = True"
    assert props["state_on_script"] == "result = 'on'"
    assert props["state_off_script"] == "result = 'off'"
    assert props["state_get_language"] == "python"
    assert props["state_on_language"] == "python"
    assert props["state_off_language"] == "python"
    assert props["state_on_label"] == "Visibility"
    assert props["state_off_label"] == "Visibility"

    triggers = matching_bindings(
        item,
        "click",
        mouse_button="left",
        modifiers=[]
    )
    assert len(triggers) == 1
    assert triggers[0]["handler"] == "state_toggle"


def test_field_multiple_defaults_to_list_display():
    item = create_item(
        "field",
        {
            "props": {"multiple": True},
        }
    )

    props = item["props"]
    assert props["multiple"] is True
    assert props["display_mode"] == "list"
    assert props["visible_rows"] == 4


def test_single_field_forces_single_line_and_single_value():
    item = create_item(
        "field",
        {
            "props": {
                "multiple": False,
                "display_mode": "list",
                "value": ["first", "second"],
            },
        }
    )

    props = item["props"]
    assert props["multiple"] is False
    assert props["display_mode"] == "single"
    assert props["value"] == "first"


def test_row_and_child_layout_settings_are_normalized():
    row = create_item(
        "row",
        {
            "props": {
                "spacing": 7,
                "equal_widths": True,
                "vertical_alignment": "bottom",
            },
            "items": [
                {
                    "kind": "button",
                    "name": "stretch_button",
                    "ui": {
                        "width_mode": "stretch",
                        "stretch": 3,
                        "alignment": "right",
                    },
                },
                {
                    "kind": "button",
                    "name": "fixed_button",
                    "ui": {
                        "width_mode": "fixed",
                        "width": 160,
                    },
                },
            ],
        }
    )

    props = row["props"]
    first_ui = row["items"][0]["ui"]
    second_ui = row["items"][1]["ui"]
    assert props["spacing"] == 7
    assert props["equal_widths"] is True
    assert props["vertical_alignment"] == "bottom"
    assert first_ui["width_mode"] == "stretch"
    assert first_ui["stretch"] == 3
    assert first_ui["alignment"] == "right"
    assert second_ui["width_mode"] == "fixed"
    assert second_ui["width"] == 160


def test_value_controls_ignore_removed_direct_script_fields():
    item = create_item(
        "integer",
        {
            "props": {
                "on_change_script": "result = value + 1",
            },
        }
    )

    assert item["bindings"] == []
    assert "on_change_script" not in item["props"]
    assert "callbacks" not in item


def test_state_query_evaluator_reads_state_variable():
    assert evaluate_python_state(
        "state = True"
    ) is True
    assert evaluate_python_state(
        "state = False"
    ) is False
