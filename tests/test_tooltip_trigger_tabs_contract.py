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


def test_trigger_tabs_use_compact_centered_solar_controls():
    source = _read(
        "scripts/script_toolbox/ui/properties/trigger_tabs.py"
    )
    package_source = _read(
        "scripts/script_toolbox/ui/properties/__init__.py"
    )

    assert 'builtin_icon("add")' in source
    assert 'builtin_icon("close")' in source
    assert '"TriggerAddButton"' in source
    assert '"TriggerCloseButton"' in source
    assert '"TriggerCloseHolder"' in source
    assert "from ..painted_icon_button import PaintedIconButton" in source
    assert "_TRIGGER_CLOSE_HOLDER_SIZE = (22, 20)" in source
    assert "_TRIGGER_CLOSE_GLYPH_SIZE = 10" in source
    assert "_TRIGGER_CLOSE_BUTTON_SIZE = 18" in source
    assert "_TRIGGER_CLOSE_OFFSET = (2, 1)" in source
    assert "_TRIGGER_ADD_GLYPH_SIZE = 12" in source
    assert "_TRIGGER_ADD_BUTTON_SIZE = 16" in source
    assert "_TRIGGER_ADD_SPACER_WIDTH = 12" in source
    assert "QtGui.QToolButton" not in source
    assert "bar.tabRect(index)" in source
    assert "(rect.width() - size.width()) // 2" in source
    assert "(rect.height() - size.height()) // 2" in source
    assert "_position_add_button" in source
    assert "QtCore.QEvent.Resize" in source
    assert "QtCore.QEvent.LayoutRequest" in source
    assert "self.tabs.setTabsClosable(False)" in source
    assert '"Add trigger"' in source
    assert "self.add_button.hide()" in source
    assert "self.tabs.setCornerWidget(" in source
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
