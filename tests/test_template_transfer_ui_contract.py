# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_import_export_buttons_are_menu_only_toolbuttons():
    source = _read(
        "scripts/script_toolbox/ui/template_transfer_hooks.py"
    )

    assert "QtGui.QToolButton.InstantPopup" in source
    assert "Import Template from File..." in source
    assert "Import Template from Clipboard" in source
    assert "Export Template to File..." in source
    assert "Copy Template to Clipboard" in source
    assert "button.clicked.disconnect" in source


def test_clipboard_transfer_uses_shared_config_codec_and_qt_clipboard():
    source = _read(
        "scripts/script_toolbox/ui/template_transfer_hooks.py"
    )
    config_source = _read(
        "scripts/script_toolbox/core/config.py"
    )

    assert "QApplication.clipboard()" in source
    assert "deserialize_config" in source
    assert "serialize_config" in source
    assert "def deserialize_config(data):" in config_source
    assert "def serialize_config(document):" in config_source
    assert "return deserialize_config(" in config_source
    assert "serialized = serialize_config(" in config_source
    assert "PySide6" not in source


def test_transfer_wrapper_is_inside_existing_telemetry_wrapper():
    source = _read(
        "scripts/script_toolbox/ui/bootstrap.py"
    )

    transfer = source.index(
        "build_template_transfer_interface_editor_class(editor_class)"
    )
    telemetry = source.index(
        "build_telemetry_interface_editor_class(editor_class)"
    )
    assert transfer < telemetry
