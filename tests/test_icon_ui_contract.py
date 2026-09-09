# -*- coding: utf-8 -*-
from __future__ import print_function

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_required_solar_icons_are_bundled():
    icon_root = (
        ROOT /
        "scripts" /
        "script_toolbox" /
        "resources" /
        "icons" /
        "solar"
    )

    for name in (
        "add.svg",
        "close.svg",
        "add-circle.svg",
        "close-circle.svg",
        "cloud-download.svg",
        "cloud-upload.svg",
        "folder-open.svg",
        "settings.svg",
    ):
        assert (icon_root / name).is_file()


def test_toolbar_icon_mappings_match_ui_contract():
    source = _read(
        "scripts/script_toolbox/style/builtin_icons.py"
    )

    assert '"update": "import"' in source
    assert '("gear", "Settings", "settings.svg")' in source
    assert '("add", "Add", "add.svg")' in source
    assert '("close", "Close", "close.svg")' in source
    assert '"cloud-download.svg"' in source
    assert '"cloud-upload.svg"' in source
    assert '"folder-open.svg"' in source


def test_share_actions_use_same_technical_icon_contract_as_import_export():
    share_source = _read(
        "scripts/script_toolbox/ui/share_hooks.py"
    )
    hook_source = _read(
        "scripts/script_toolbox/ui/icon_ui_hooks.py"
    )

    assert 'button.setObjectName("IconButton")' in share_source
    assert "button._script_toolbox_share_role = share_role" in share_source
    assert '"SharePasteButton": "cloud-download"' in hook_source
    assert '"ShareButton": "cloud-upload"' in hook_source
    assert '"_script_toolbox_share_role"' in hook_source


def test_icon_ui_hooks_are_wired():
    hook_source = _read(
        "scripts/script_toolbox/ui/icon_ui_hooks.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "QFileDialog.getOpenFileName" in hook_source
    assert "solar_icon_directory()" in hook_source
    assert 'toolbar_icon("delete")' in hook_source
    assert "install_property_icon_browse(" in ui_source
    assert "install_script_editor_icons(" in ui_source
    assert "build_icon_interface_editor_class(" in ui_source
