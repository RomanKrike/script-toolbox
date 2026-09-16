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
    assert "Import Template / Item from Clipboard" in source
    assert "Paste Shared Toolbox from Clipboard" in source
    assert "Export Template to File..." in source
    assert "Copy Template to Clipboard" in source
    assert "Share Toolbox and Copy STB1 Code" in source
    assert "menu.addSeparator()" in source
    assert "button.clicked.disconnect" in source


def test_legacy_whole_toolbox_share_buttons_are_removed_from_toolbar():
    source = _read(
        "scripts/script_toolbox/ui/template_transfer_hooks.py"
    )

    assert "def _remove_redundant_share_buttons(editor):" in source
    assert '"share_paste_button"' in source
    assert '"share_button"' in source
    assert "layout.removeWidget(" in source
    assert "button.setParent(" in source
    assert "button.deleteLater()" in source
    assert "_remove_redundant_share_buttons(" in source


def test_whole_toolbox_share_actions_still_use_existing_share_controller():
    source = _read(
        "scripts/script_toolbox/ui/template_transfer_hooks.py"
    )
    share_source = _read(
        "scripts/script_toolbox/ui/share_hooks.py"
    )

    assert "self.paste_shared_settings" in source
    assert "self.share_settings" in source
    assert "def paste_shared_settings(self):" in share_source
    assert "def share_settings(self):" in share_source
    assert "fetch_shared_data(code)" in share_source
    assert 'share_data(\n                "config",' in share_source


def test_clipboard_transfer_uses_shared_config_codec_and_qt_clipboard():
    source = _read(
        "scripts/script_toolbox/ui/template_transfer_hooks.py"
    )
    config_source = _read(
        "scripts/script_toolbox/core/config.py"
    )

    assert "QApplication.clipboard()" in source
    assert "deserialize_transfer" in source
    assert "serialize_config" in source
    assert "def deserialize_config(data):" in config_source
    assert "def deserialize_transfer(data):" in config_source
    assert "def serialize_config(document):" in config_source
    assert "return deserialize_config(" in config_source
    assert "serialized = serialize_config(" in config_source
    assert "PySide6" not in source


def test_clipboard_item_transfer_uses_normal_editor_insert_path():
    source = _read(
        "scripts/script_toolbox/ui/template_transfer_hooks.py"
    )
    config_source = _read(
        "scripts/script_toolbox/core/config.py"
    )

    assert 'if transfer_kind == "item":' in source
    assert "self._apply_item_import(" in source
    assert "self._insert_cloned_tree_item(" in source
    assert "self._clone_data(" in source
    assert "create_item(" in config_source


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
