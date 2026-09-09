# -*- coding: utf-8 -*-
from __future__ import print_function

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_search_ux_is_not_owned_by_editor_polish_hooks():
    source = _read(
        "scripts/script_toolbox/ui/editor_polish_hooks.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "install_editor_search_ux" not in source
    assert "SearchFieldDecorationFilter" not in source
    assert "_EXISTING_FILTER_STYLE" not in source
    assert "_TECH_ICON_STYLE" not in source
    assert "EditorSearchIcon" not in source
    assert "EditorSearchClear" not in source
    assert "_search_control(" not in source
    assert "install_editor_search_ux" not in ui_source
    assert "build_search_interface_editor_class" in ui_source


def test_button_without_visible_label_uses_exact_centered_icon_renderer():
    source = _read(
        "scripts/script_toolbox/ui/editor_polish_hooks.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "class CenteredIconPushButton" in source
    assert "def paintEvent(self, event):" in source
    assert "QtGui.QPushButton.paintEvent(" in source
    assert "(self.width() - width) // 2" in source
    assert "(self.height() - height) // 2" in source
    assert "self._centered_icon.paint(" in source
    assert "icon.pixmap(" not in source
    assert "_button_should_center_icon(" in source
    assert 'item.get("icon_path")' in source
    assert 'item.get("icon_only", False)' in source
    assert 'item.get("show_label", True)' in source
    assert "_render_centered_icon_button(" in source
    assert "install_icon_only_state_refresh(" in source
    assert "widget.setText(\"\")" in source
    assert "install_icon_only_state_refresh(" in ui_source

    install_center = ui_source.rindex(
        "install_icon_only_button_centering("
    )
    install_bindings = ui_source.rindex(
        "install_event_binding_hooks("
    )
    assert install_center < install_bindings


def test_editor_polish_theme_colors_use_shared_palette():
    source = _read(
        "scripts/script_toolbox/ui/editor_polish_hooks.py"
    )

    assert "from ..style import palette" in source
    assert "palette.ICON_BUTTON_HOVER_BG" in source
    assert "palette.ICON_BUTTON_HOVER_BORDER" in source
    assert "palette.ICON_BUTTON_PRESSED_BG" in source
    assert "palette.BORDER_INSET" in source

    # Theme colors must come from style/palette.py. Dynamic user-configurable
    # button colors remain rgb(...) values and are intentionally local.
    assert re.search(r"#[0-9a-fA-F]{6}\b", source) is None


def test_runtime_icon_feedback_matches_technical_icon_states():
    source = _read(
        "scripts/script_toolbox/ui/editor_polish_hooks.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "class IconFeedbackFilter" in source
    assert "QtCore.QEvent.Enter" in source
    assert "QtCore.QEvent.Leave" in source
    assert "QtCore.QEvent.MouseButtonPress" in source
    assert "QtCore.QEvent.MouseButtonRelease" in source
    assert "palette.ICON_BUTTON_HOVER_BG" in source
    assert "palette.ICON_BUTTON_HOVER_BORDER" in source
    assert "palette.ICON_BUTTON_PRESSED_BG" in source
    assert "palette.BORDER_INSET" in source
    assert "install_runtime_icon_feedback(" in source
    assert "install_runtime_icon_feedback(" in ui_source
