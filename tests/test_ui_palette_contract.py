# -*- coding: utf-8 -*-

import os
import re


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

_THEME_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")
_FIXED_QCOLOR_STRING = re.compile(
    r"QtGui\.QColor\(\s*['\"][^'\"]+['\"]\s*\)"
)
_FIXED_QCOLOR_RGB = re.compile(
    r"QtGui\.QColor\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)"
)


def _read(relative_path):
    path = os.path.join(
        ROOT,
        *relative_path.split("/")
    )
    with open(path, "r") as handle:
        return handle.read()


def _uses_qcolor(source, token):
    return re.search(
        r"QtGui\.QColor\(\s*{0}\s*\)".format(token),
        source
    ) is not None


def _theme_python_paths():
    roots = (
        os.path.join(
            ROOT,
            "scripts",
            "script_toolbox",
            "ui"
        ),
        os.path.join(
            ROOT,
            "scripts",
            "script_toolbox",
            "style"
        ),
    )
    palette_path = os.path.normpath(
        os.path.join(
            ROOT,
            "scripts",
            "script_toolbox",
            "style",
            "palette.py"
        )
    )

    for source_root in roots:
        for directory, unused_dirs, filenames in os.walk(source_root):
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                path = os.path.normpath(
                    os.path.join(directory, filename)
                )
                if path == palette_path:
                    continue
                yield path


def test_ui_and_style_modules_do_not_define_fixed_theme_colors():
    violations = []

    for path in _theme_python_paths():
        with open(path, "r") as handle:
            source = handle.read()

        matches = []
        matches.extend(
            _THEME_HEX.findall(source)
        )
        matches.extend(
            _FIXED_QCOLOR_STRING.findall(source)
        )
        matches.extend(
            _FIXED_QCOLOR_RGB.findall(source)
        )

        if matches:
            violations.append((
                os.path.relpath(path, ROOT),
                matches
            ))

    assert not violations, violations


def test_primary_ui_modules_use_semantic_palette_tokens():
    interface_source = _read(
        "scripts/script_toolbox/ui/interface_editor.py"
    )
    main_source = _read(
        "scripts/script_toolbox/ui/main_window.py"
    )
    property_source = _read(
        "scripts/script_toolbox/ui/properties/base.py"
    )
    palette_source = _read(
        "scripts/script_toolbox/style/palette.py"
    )

    assert "from ..style.palette import WINDOW_BG" in interface_source
    assert "from ..style.palette import TEXT_PALETTE_GROUP" in interface_source
    assert "from ..style.palette import STRUCTURE_FOLDER_BG" in interface_source
    assert "from ..style.palette import TEXT_STRUCTURE_ROW" in interface_source
    assert _uses_qcolor(interface_source, "WINDOW_BG")
    assert _uses_qcolor(interface_source, "TEXT_PALETTE_GROUP")
    assert _uses_qcolor(interface_source, "STRUCTURE_FOLDER_BG")
    assert _uses_qcolor(interface_source, "TEXT_STRUCTURE_ROW")

    assert "from ..style.palette import CONTENT_BG" in main_source
    assert '"background-color: {0};".format(' in main_source
    assert "CONTENT_BG" in main_source

    assert "from ...style.palette import WINDOW_BG" in property_source
    assert _uses_qcolor(property_source, "WINDOW_BG")

    assert 'CONTENT_BG = WINDOW_BG' in palette_source
    assert 'STRUCTURE_FOLDER_BG = "#302d2a"' in palette_source
    assert 'TEXT_PALETTE_GROUP = "#bda88f"' in palette_source
    assert 'TEXT_STRUCTURE_ROW = "#b6c4cf"' in palette_source
    assert 'TEXT_STRUCTURE_COLUMN = "#c7b7d7"' in palette_source


def test_runtime_surfaces_alias_interface_editor_neutrals():
    palette_source = _read(
        "scripts/script_toolbox/style/palette.py"
    )

    for expected in (
        "CONTENT_BG = WINDOW_BG",
        "FOLDER_CARD_BG = PANEL_BG",
        "FOLDER_NESTED_BG = PANEL_BG",
        "FOLDER_HEADER_BG = PANEL_BG",
        "FOLDER_HEADER_HOVER_BG = ICON_BUTTON_HOVER_BG",
        "FOLDER_HEADER_PRESSED_BG = BUTTON_PRESSED_BG",
        "FOLDER_HEADER_COLLAPSED_BG = PANEL_BG",
        "FOLDER_NESTED_HEADER_BG = PANEL_BG",
        "FOLDER_NESTED_HEADER_HOVER_BG = ICON_BUTTON_HOVER_BG",
        "FOLDER_NESTED_HEADER_COLLAPSED_BG = PANEL_BG",
        "SIMPLE_SECTION_NESTED_BG = PANEL_BG",
    ):
        assert expected in palette_source


def test_code_editor_and_legacy_icons_use_palette_tokens():
    editor_source = _read(
        "scripts/script_toolbox/ui/code_editor.py"
    )
    icons_source = _read(
        "scripts/script_toolbox/style/icons.py"
    )
    layout_source = _read(
        "scripts/script_toolbox/ui/layout_editor_adapter.py"
    )

    assert "CODE_GUTTER_BG" in editor_source
    assert "CODE_CURRENT_LINE_BG" in editor_source
    assert "SYNTAX_KEYWORD" in editor_source
    assert "SYNTAX_STRING" in editor_source
    assert "SYNTAX_COMMENT" in editor_source
    assert "SYNTAX_NUMBER" in editor_source
    assert "SYNTAX_HOST" in editor_source

    assert "from .palette import TOOLBAR_ICON" in icons_source
    assert "QtGui.QColor(TOOLBAR_ICON)" in icons_source

    assert "TEXT_STRUCTURE_COLUMN" in layout_source
    assert "QtGui.QColor(TEXT_STRUCTURE_COLUMN)" in layout_source


def test_solar_toolbar_icons_are_tinted_from_shared_palette():
    source = _read(
        "scripts/script_toolbox/style/builtin_icons.py"
    )
    palette_source = _read(
        "scripts/script_toolbox/style/palette.py"
    )

    assert "from .palette import TOOLBAR_ICON" in source
    assert "QtGui.QColor(TOOLBAR_ICON)" in source
    assert "CompositionMode_SourceIn" in source
    assert "painter.fillRect(" in source
    assert "_tinted_icon(resource)" in source
    assert "TOOLBAR_ICON = TEXT_PRIMARY" in palette_source
