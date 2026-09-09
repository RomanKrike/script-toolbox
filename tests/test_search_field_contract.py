# -*- coding: utf-8 -*-
from __future__ import print_function

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_search_field_owns_embedded_solar_controls_and_geometry():
    source = _read(
        "scripts/script_toolbox/ui/search_field.py"
    )

    assert "class SearchField(QtGui.QLineEdit):" in source
    assert 'self.setObjectName(\n            "SearchField"' in source
    assert "from .painted_icon_button import PaintedIconButton" in source
    assert '"SearchFieldIcon"' in source
    assert '"SearchFieldClear"' in source
    assert 'builtin_icon("find")' in source
    assert 'builtin_icon("close")' in source
    assert "PaintedIconButton(" in source
    assert "_SEARCH_ICON_SIZE = 18" in source
    assert "_CLEAR_BUTTON_SIZE = 20" in source
    assert "self.setTextMargins(" in source
    assert "26," in source
    assert "30," in source
    assert "self.clear_button.clicked.connect(" in source
    assert "self.clear" in source
    assert "def resizeEvent(self, event):" in source
    assert "def showEvent(self, event):" in source
    assert "self.search_icon.move(" in source
    assert "self.clear_button.move(" in source
    assert "installEventFilter(" not in source
    assert "QtGui.QToolButton" not in source


def test_painted_search_controls_keep_qt4_clip_workaround_palette_driven():
    source = _read(
        "scripts/script_toolbox/ui/painted_icon_button.py"
    )

    assert "class PaintedIconButton(QtGui.QWidget):" in source
    assert "self._icon.paint(" in source
    assert "self._icon_rect()" in source
    assert "QtGui.QToolButton" not in source
    assert "palette.ICON_BUTTON_PRESSED_BG" in source
    assert "palette.BORDER_INSET" in source
    assert "palette.ICON_BUTTON_HOVER_BG" in source
    assert "palette.ICON_BUTTON_HOVER_BORDER" in source
    assert re.search(r"#[0-9a-fA-F]{6}\b", source) is None


def test_editor_search_exposes_reusable_helpers_for_both_lists():
    source = _read(
        "scripts/script_toolbox/ui/editor_search.py"
    )

    assert "from .search_field import SearchField" in source
    assert "def install_editor_search(editor):" in source
    assert "def filter_existing_parameters(editor, value):" in source
    assert "def reapply_existing_filter(editor):" in source
    assert "def apply_editor_presentation(editor):" in source
    assert 'SearchField(\n            "Filter parameters..."' in source
    assert 'SearchField(\n            "Filter existing parameters..."' in source
    assert 'editor.search_fields[\n            "palette"' in source
    assert 'editor.search_fields[\n            "structure"' in source
    assert "editor.palette_search_control = editor.palette_filter" in source
    assert "editor.existing_search_control = editor.existing_filter" in source
    assert "_filter_tree_branch(" in source
    assert "child_match" in source


def test_editor_presentation_is_composed_without_search_wrapper():
    search_source = _read(
        "scripts/script_toolbox/ui/editor_search.py"
    )
    adapter_source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "from .editor_scroll_frames import install_interface_editor_scroll_frames" in search_source
    assert "from .property_pane_style import apply_property_pane_style" in search_source
    assert "apply_property_pane_style(editor)" in search_source
    assert "install_interface_editor_scroll_frames(editor)" in search_source

    assert "from .editor_search import apply_editor_presentation" in adapter_source
    assert "apply_editor_presentation(self)" in adapter_source
    assert "from .editor_search import filter_existing_parameters as filter_editor_structure" in adapter_source
    assert "from .editor_search import reapply_existing_filter" in adapter_source

    assert "build_search_interface_editor_class(" not in ui_source
    assert "from .editor_search" not in ui_source
    assert "build_scroll_frame_interface_editor_class" not in ui_source
    assert "install_property_pane_style" not in ui_source
    assert "PropertyEditorBase" not in ui_source


def test_existing_filter_is_reapplied_after_tree_rebuild():
    search_source = _read(
        "scripts/script_toolbox/ui/editor_search.py"
    )
    adapter_source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )

    assert "def reapply_existing_filter(editor):" in search_source
    assert "filter_existing_parameters(" in search_source
    assert "search.text()" in search_source

    populate_source = adapter_source.split(
        "        def populate_tree(self):",
        1
    )[1].split(
        "        # --------------------------------------------------------------\n"
        "        # Document ownership compatibility",
        1
    )[0]

    assert "base_class.populate_tree(" in populate_source
    assert "reapply_existing_filter(self)" in populate_source


def test_search_component_styles_are_centralized_and_palette_driven():
    source = _read(
        "scripts/script_toolbox/style/components.py"
    )
    style_init = _read(
        "scripts/script_toolbox/style/__init__.py"
    )

    assert "QLineEdit#SearchField" in source
    assert "%(FILTER_BG)s" in source
    assert "%(BORDER_SOFT)s" in source
    assert "%(FOCUS_BORDER)s" in source
    assert "SearchFieldIcon" not in source
    assert "SearchFieldClear" not in source
    assert re.search(r"#[0-9a-fA-F]{6}\b", source) is None

    assert "from .components import COMPONENT_STYLES" in style_init
    assert "BASE_STYLE + COMPONENT_STYLES + RUNTIME_OVERRIDES" in style_init
