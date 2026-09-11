# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_simple_section_reuses_runtime_folder_and_shared_theme_contract():
    runtime = _read("scripts/script_toolbox/ui/runtime.py")
    stylesheet = _read("scripts/script_toolbox/style/stylesheet.py")
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    palette = _read("scripts/script_toolbox/style/palette.py")

    # The existing Simple Section renderer remains RuntimeFolder; the change is
    # presentation-only and does not introduce another item/container type.
    assert 'self.folder_type = section.get("folder_type", "collapsible")' in runtime
    assert 'self.header.setObjectName("SimpleSectionHeader")' in runtime
    assert 'title.setObjectName("SectionTitle")' in runtime

    # The frame is composed from the existing header/content surfaces so the
    # title can visually interrupt the top edge like a QGroupBox legend.
    assert 'QFrame#RuntimeFolder[folderType="simple"] > QFrame#SimpleSectionHeader {' in stylesheet
    assert 'QFrame#RuntimeFolder[folderType="simple"] > QWidget#RuntimeFolderContent {' in stylesheet
    assert 'border: 1px solid %(BORDER_GROUP)s;' in stylesheet
    assert 'background-color: %(CONTENT_BG)s;' in stylesheet
    assert 'background-color: %(SIMPLE_SECTION_NESTED_BG)s;' in stylesheet

    # Nested Simple Sections must not keep the old outer card border in
    # addition to the composed group-box frame.
    nested_rule = (
        'QFrame#RuntimeFolder[folderType="simple"][nested="true"] {\n'
        '    background-color: %(FOLDER_NESTED_BG)s;\n'
        '    border: 0px;\n'
        '}'
    )
    assert nested_rule in stylesheet

    # Empty titles keep a continuous top line instead of leaving a blank notch.
    assert 'QLabel#SectionTitle[text=""] {' in stylesheet
    assert 'padding-left: 0px;' in stylesheet
    assert 'padding-right: 0px;' in stylesheet

    # Geometry and colors remain centralized rather than hard-coded locally.
    assert 'RUNTIME_SIMPLE_HEADER_MARGINS = (8, 0, 5, 0)' in metrics
    assert 'BORDER_GROUP = "#414141"' in palette
    assert 'TEXT_SECTION = TEXT_PRIMARY' in palette
    assert 'SIMPLE_SECTION_NESTED_BG = PANEL_BG' in palette
