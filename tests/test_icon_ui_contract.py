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


def test_technical_icon_buttons_use_shared_factory_and_presets():
    source = _read(
        "scripts/script_toolbox/ui/icon_button.py"
    )

    assert 'ICON_BUTTON_COMPACT = "compact"' in source
    assert 'ICON_BUTTON_TOOLBAR = "toolbar"' in source
    assert 'ICON_BUTTON_HEADER = "header"' in source
    assert "ICON_BUTTON_COMPACT: (16, 25)" in source
    assert "ICON_BUTTON_TOOLBAR: (18, 26)" in source
    assert "ICON_BUTTON_HEADER: (18, 28)" in source
    assert 'button.setObjectName("IconButton")' in source
    assert "toolbar_icon(icon_name)" in source
    assert "button.setIconSize(" in source
    assert "button.setFixedSize(" in source


def test_main_header_uses_shared_icon_button_factory():
    source = _read(
        "scripts/script_toolbox/ui/main_window.py"
    )

    assert "ICON_BUTTON_HEADER" in source
    assert "create_icon_button(" in source
    assert "self.check_updates_button = create_icon_button(" in source
    assert "self.reload_button = create_icon_button(" in source
    assert "self.interface_editor_button = create_icon_button(" in source
    assert "check_updates_button = QtGui.QToolButton()" not in source
    assert "reload_button = QtGui.QToolButton()" not in source
    assert "gear = QtGui.QToolButton()" not in source


def test_interface_editor_uses_shared_icon_button_factory():
    source = _read(
        "scripts/script_toolbox/ui/interface_editor.py"
    )

    assert "ICON_BUTTON_COMPACT" in source
    assert "create_icon_button(" in source
    assert "self.structure_toolbar_buttons = {}" in source
    assert "toolbar_icon(" not in source
    assert "button = QtGui.QToolButton()" not in source
    assert "return create_icon_button(" in source


def test_share_actions_use_stable_references_and_final_icons():
    share_source = _read(
        "scripts/script_toolbox/ui/share_hooks.py"
    )

    assert "create_icon_button(" in share_source
    assert "self.export_button" in share_source
    assert "self.share_paste_button" in share_source
    assert "self.share_button" in share_source
    assert "self.share_action_widget" in share_source
    assert "self.share_action_layout" in share_source
    assert 'cluster.setObjectName("ShareActionCluster")' in share_source
    assert '"cloud-download"' in share_source
    assert '"cloud-upload"' in share_source
    assert "_script_toolbox_share_role" not in share_source
    assert ".toolTip()" not in share_source
    assert "def _layout_for_widget(" not in share_source
    assert "itemAt(" not in share_source
    assert "findChildren(" not in share_source
    assert "_install_share_buttons" not in share_source


def test_script_editor_creates_final_clear_output_button_directly():
    source = _read(
        "scripts/script_toolbox/ui/script_editor.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "ICON_BUTTON_TOOLBAR" in source
    assert "create_icon_button(" in source
    assert "self.clear_output_button" in source
    assert '"delete"' in source
    assert "install_script_editor_icons(" not in ui_source
    assert "build_icon_interface_editor_class(" not in ui_source


def test_property_icon_browse_is_installed_directly_by_editors():
    browse_source = _read(
        "scripts/script_toolbox/ui/icon_browse.py"
    )
    hook_source = _read(
        "scripts/script_toolbox/ui/icon_ui_hooks.py"
    )
    button_source = _read(
        "scripts/script_toolbox/ui/properties/button.py"
    )
    icon_source = _read(
        "scripts/script_toolbox/ui/properties/icon.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "QFileDialog.getOpenFileName" in browse_source
    assert "solar_icon_directory()" in browse_source
    assert "create_icon_button(" in browse_source
    assert "configure_inline_layout(" in browse_source

    assert "from ..icon_browse import install_icon_browse" in button_source
    assert "self.icon_browse_button = install_icon_browse(" in button_source
    assert "from ..icon_browse import install_icon_browse" in icon_source
    assert "self.icon_browse_button = install_icon_browse(" in icon_source

    assert "install_property_icon_browse(" not in ui_source
    assert "from .icon_ui_hooks" not in ui_source
    assert ".__init__ =" not in hook_source
    assert "def install_property_icon_browse(" in hook_source
