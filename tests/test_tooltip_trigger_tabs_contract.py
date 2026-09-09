# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(
        ROOT,
        *relative_path.split("/")
    )
    with open(path, "r") as handle:
        return handle.read()


def test_runtime_tooltip_override_avoids_qss_padding_geometry_bug():
    source = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )

    tooltip_rule = source.split(
        "QToolTip {",
        1
    )[1].split(
        "}",
        1
    )[0]

    assert "padding: 0px;" in tooltip_rule


def test_trigger_add_action_is_installed_as_trailing_solar_tab():
    source = _read(
        "scripts/script_toolbox/ui/properties/trigger_tabs.py"
    )
    package_source = _read(
        "scripts/script_toolbox/ui/properties/__init__.py"
    )

    assert 'self.tabs.addTab(' in source
    assert 'builtin_icon("add-circle")' in source
    assert 'builtin_icon("close-circle")' in source
    assert "self.tabs.setTabsClosable(False)" in source
    assert '"Add trigger"' in source
    assert "self.add_button.hide()" in source
    assert "self.tabs.setCornerWidget(" in source
    assert "None," in source
    assert "index == add_index" in source
    assert "QtCore.QTimer.singleShot(" in source
    assert "install_integrated_trigger_tabs()" in package_source


def test_trigger_add_tab_stays_after_real_binding_pages():
    source = _read(
        "scripts/script_toolbox/ui/properties/trigger_tabs.py"
    )

    add_page_source = source.split(
        "    def _add_page(self, binding):",
        1
    )[1].split(
        "    def eventFilter",
        1
    )[0]

    assert "self._remove_add_tab()" in add_page_source
    assert "_BaseBindingPanel._add_page(" in add_page_source
    assert "self._install_trigger_close_button(" in add_page_source
    assert "self._ensure_add_tab()" in add_page_source


def test_property_script_editor_is_large_expanding_and_resizable():
    source = _read(
        "scripts/script_toolbox/ui/properties/script_editor_sizing.py"
    )
    package_source = _read(
        "scripts/script_toolbox/ui/properties/__init__.py"
    )

    assert "_DEFAULT_SCRIPT_EDITOR_HEIGHT = 480" in source
    assert "_MIN_SCRIPT_EDITOR_HEIGHT = 240" in source
    assert "_MAX_SCRIPT_EDITOR_HEIGHT = 1600" in source
    assert "class ScriptEditorResizeHandle" in source
    assert '"Drag to resize script editor"' in source
    assert "QtCore.Qt.SizeVerCursor" in source
    assert "event.globalY()" in source
    assert "_set_panel_script_editor_height(" in source
    assert "QtGui.QSizePolicy.Expanding" in source
    assert "self.root_layout.setStretch(" in source
    assert "self.binding_panel" in source
    assert "install_expanding_script_editors()" in package_source
