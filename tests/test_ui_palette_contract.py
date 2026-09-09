# -*- coding: utf-8 -*-

import os
import re


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

_THEME_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


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


def test_primary_ui_modules_do_not_define_theme_hex_colors():
    for relative_path in (
        "scripts/script_toolbox/ui/interface_editor.py",
        "scripts/script_toolbox/ui/main_window.py",
        "scripts/script_toolbox/ui/properties/base.py",
    ):
        source = _read(relative_path)
        assert not _THEME_HEX.findall(source), relative_path


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

    assert 'STRUCTURE_FOLDER_BG = "#302d2a"' in palette_source
    assert 'TEXT_PALETTE_GROUP = "#bda88f"' in palette_source
    assert 'TEXT_STRUCTURE_ROW = "#b6c4cf"' in palette_source
