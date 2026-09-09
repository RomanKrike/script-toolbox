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
    assert '"SearchFieldIcon"' in source
    assert '"SearchFieldClear"' in source
    assert 'builtin_icon("find")' in source
    assert 'builtin_icon("close")' in source
    assert "QtCore.QSize(9, 9)" in source
    assert "_SEARCH_ICON_SIZE = 18" in source
    assert "_CLEAR_BUTTON_SIZE = 20" in source
    assert "self.setTextMargins(" in source
    assert "self.clear_button.clicked.connect(" in source
    assert "self.clear" in source
    assert "def resizeEvent(self, event):" in source
    assert "def showEvent(self, event):" in source
    assert "self.search_icon.move(" in source
    assert "self.clear_button.move(" in source
    assert "installEventFilter(" not in source


def test_interface_editor_uses_one_search_component_for_both_lists():
    source = _read(
        "scripts/script_toolbox/ui/editor_search.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "from .search_field import SearchField" in source
    assert "build_search_interface_editor_class" in source
    assert 'SearchField(\n                    "Filter parameters..."' in source
    assert 'SearchField(\n                    "Filter existing parameters..."' in source
    assert 'self.search_fields[\n                    "palette"' in source
    assert 'self.search_fields[\n                    "structure"' in source
    assert "self.palette_search_control = self.palette_filter" in source
    assert "self.existing_search_control = self.existing_filter" in source
    assert "self.filter_existing_parameters(" in source
    assert "_filter_tree_branch(" in source
    assert "child_match" in source

    assert "build_search_interface_editor_class" in ui_source
    assert "install_editor_search_ux" not in ui_source


def test_existing_filter_is_reapplied_after_tree_rebuild():
    source = _read(
        "scripts/script_toolbox/ui/editor_search.py"
    )

    populate_source = source.split(
        "        def populate_tree(self):",
        1
    )[1].split(
        "    InterfaceEditor.__name__",
        1
    )[0]

    assert "base_class.populate_tree(" in populate_source
    assert "self.filter_existing_parameters(" in populate_source
    assert "search.text()" in populate_source


def test_search_component_styles_are_centralized_and_palette_driven():
    source = _read(
        "scripts/script_toolbox/style/components.py"
    )
    style_init = _read(
        "scripts/script_toolbox/style/__init__.py"
    )

    assert "QLineEdit#SearchField" in source
    assert "QToolButton#SearchFieldIcon" in source
    assert "QToolButton#SearchFieldClear" in source
    assert "%(FILTER_BG)s" in source
    assert "%(BORDER_SOFT)s" in source
    assert "%(FOCUS_BORDER)s" in source
    assert "%(ICON_BUTTON_HOVER_BG)s" in source
    assert "%(ICON_BUTTON_PRESSED_BG)s" in source
    assert re.search(r"#[0-9a-fA-F]{6}\b", source) is None

    assert "from .components import COMPONENT_STYLES" in style_init
    assert "BASE_STYLE + COMPONENT_STYLES + RUNTIME_OVERRIDES" in style_init
