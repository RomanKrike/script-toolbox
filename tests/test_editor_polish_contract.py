# -*- coding: utf-8 -*-
from __future__ import print_function

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_create_and_existing_search_fields_use_embedded_solar_controls():
    source = _read(
        "scripts/script_toolbox/ui/editor_polish_hooks.py"
    )

    assert "_hide_palette_hint(" in source
    assert '"HintText"' in source
    assert "_search_control(" in source
    assert 'builtin_icon("find")' in source
    assert 'builtin_icon("close")' in source
    assert '"EditorSearchIcon"' in source
    assert '"EditorSearchClear"' in source
    assert "QtGui.QToolButton(\n        line_edit" in source
    assert "line_edit.setTextMargins(" in source
    assert "class SearchFieldDecorationFilter" in source
    assert "QtCore.QEvent.Resize" in source
    assert "search_icon.move(" in source
    assert "clear_button.move(" in source
    assert "clear_button.clicked.connect(" in source
    assert "line_edit.clear" in source
    assert "palette_search_control" in source
    assert "existing_search_control" in source
    assert '"ExistingParametersFilter"' in source
    assert '"Filter existing parameters..."' in source
    assert "self.filter_existing_parameters" in source
    assert "_filter_tree_branch(" in source
    assert "child_match" in source


def test_existing_parameter_filter_is_reapplied_after_tree_rebuild():
    source = _read(
        "scripts/script_toolbox/ui/editor_polish_hooks.py"
    )

    populate_source = source.split(
        "    def populate_tree(self):",
        1
    )[1].split(
        "    editor_class.filter_existing_parameters",
        1
    )[0]

    assert "original_populate_tree(self)" in populate_source
    assert "self.filter_existing_parameters(" in populate_source


def test_icon_only_button_paints_qicon_at_exact_widget_center():
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
    assert "QtGui.QHBoxLayout(" not in source
    assert "_render_centered_icon_button(" in source
    assert 'bool(\n            item.get("icon_only", False)' in source
    assert "install_icon_only_state_refresh(" in source
    assert "widget.setText(\"\")" in source
    assert "install_icon_only_state_refresh(" in ui_source
    assert ui_source.index(
        "install_icon_only_button_centering("
    ) < ui_source.index(
        "install_event_binding_hooks("
    )


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
    assert "background-color: #404040;" in source
    assert "border: 1px solid #545454;" in source
    assert "background-color: #272727;" in source
    assert "install_runtime_icon_feedback(" in source
    assert "install_runtime_icon_feedback(" in ui_source
