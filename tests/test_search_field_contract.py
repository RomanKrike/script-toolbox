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
    metrics = _read(
        "scripts/script_toolbox/style/metrics.py"
    )

    assert "class SearchField(QtGui.QLineEdit):" in source
    assert 'self.setObjectName(\n            "SearchField"' in source
    assert "from .painted_icon_button import PaintedIconButton" in source
    assert '"SearchFieldIcon"' in source
    assert '"SearchFieldClear"' in source
    assert 'builtin_icon("find")' in source
    assert 'builtin_icon("close")' in source
    assert "PaintedIconButton(" in source
    assert "SEARCH_ICON_SIZE = 18" in metrics
    assert "SEARCH_CLEAR_SIZE = 20" in metrics
    assert "SEARCH_TEXT_MARGIN_LEFT = 26" in metrics
    assert "SEARCH_TEXT_MARGIN_RIGHT = 30" in metrics
    assert "SEARCH_ICON_SIZE" in source
    assert "SEARCH_CLEAR_SIZE" in source
    assert "SEARCH_TEXT_MARGIN_LEFT" in source
    assert "SEARCH_TEXT_MARGIN_RIGHT" in source
    assert "self.setTextMargins(" in source
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


def test_interface_editor_builds_shared_search_fields_directly():
    editor_source = _read(
        "scripts/script_toolbox/ui/interface_editor.py"
    )
    search_source = _read(
        "scripts/script_toolbox/ui/editor_search.py"
    )
    base_style_source = _read(
        "scripts/script_toolbox/style/stylesheet.py"
    )

    assert "from .search_field import SearchField" in editor_source
    assert "self.search_fields = {}" in editor_source
    assert 'SearchField(\n            "Filter parameters..."' in editor_source
    assert 'SearchField(\n            "Filter existing parameters..."' in editor_source
    assert "self.palette_search_control = self.palette_filter" in editor_source
    assert "self.existing_search_control = self.existing_filter" in editor_source
    assert 'self.search_fields[\n            "palette"' in editor_source
    assert 'self.search_fields[\n            "structure"' in editor_source
    assert "self.palette_filter.textChanged.connect(" in editor_source
    assert "self.existing_filter.textChanged.connect(" in editor_source
    assert '"PaletteFilter"' not in editor_source
    assert '"HintText"' not in editor_source

    build_source = editor_source.split(
        "    def build_ui(self):",
        1
    )[1].split(
        "    def _icon_button(",
        1
    )[0]
    assert build_source.index(
        "left_layout.addWidget(\n            self.palette,"
    ) < build_source.index(
        "self.palette_filter = SearchField("
    )
    assert build_source.index(
        "center_layout.addWidget(\n            self.tree,"
    ) < build_source.index(
        "self.existing_filter = SearchField("
    )

    assert "def filter_existing_parameters(editor, value):" in search_source
    assert "def reapply_existing_filter(editor):" in search_source
    assert "def apply_editor_presentation(editor):" in search_source
    assert "_filter_tree_branch(" in search_source
    assert "child_match" in search_source
    assert "def install_editor_search(editor):" not in search_source
    assert "_hide_legacy_palette_hint" not in search_source
    assert "findChildren(" not in search_source
    assert "SearchField(" not in search_source

    assert "QLineEdit#PaletteFilter" not in base_style_source
    assert "QLabel#HintText" not in base_style_source


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
    assert "%(SEARCH_FIELD_MIN_HEIGHT)s" in source
    assert "%(BORDER_RADIUS_CONTROL)s" in source
    assert "SearchFieldIcon" not in source
    assert "SearchFieldClear" not in source
    assert re.search(r"#[0-9a-fA-F]{6}\b", source) is None

    assert "from .components import COMPONENT_STYLES" in style_init
    assert "BASE_STYLE + COMPONENT_STYLES + RUNTIME_OVERRIDES" in style_init
