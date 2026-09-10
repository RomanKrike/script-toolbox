# -*- coding: utf-8 -*-

from pathlib import Path

from script_toolbox.model import create_item


ROOT = Path(__file__).resolve().parents[1]


def test_text_item_normalizes_static_multiline_content():
    item = create_item(
        "text",
        {
            "text": "First line\nSecond line",
            "show_label": True,
            "bindings": [
                {
                    "event": "click",
                    "script": "print('unexpected')",
                }
            ],
        }
    )

    assert item["kind"] == "text"
    assert item["text"] == "First line\nSecond line"
    assert item["show_label"] is False
    assert item["bindings"] == []


def test_text_item_preserves_intentional_empty_content():
    item = create_item(
        "text",
        {
            "text": "",
        }
    )

    assert item["text"] == ""


def test_text_runtime_contract_uses_palette_and_word_wrap():
    source = (
        ROOT /
        "scripts" /
        "script_toolbox" /
        "ui" /
        "text_runtime.py"
    ).read_text(encoding="utf-8")

    assert "TEXT_SUBTLE" in source
    assert "setWordWrap(True)" in source
    assert "QtCore.Qt.PlainText" in source
    assert "background" not in source.lower()
    assert "border" not in source.lower()


def test_text_property_editor_uses_shared_multiline_metric():
    source = (
        ROOT /
        "scripts" /
        "script_toolbox" /
        "ui" /
        "properties" /
        "text.py"
    ).read_text(encoding="utf-8")

    assert "metrics.PROPERTY_MULTILINE_TEXT_MIN_HEIGHT" in source


def test_text_item_is_registered_in_editor_palette_and_runtime():
    source = (
        ROOT /
        "scripts" /
        "script_toolbox" /
        "ui" /
        "__init__.py"
    ).read_text(encoding="utf-8")

    assert '"Text",' in source
    assert '"text",' in source
    assert 'register_runtime_renderer("text", render_text)' in source
