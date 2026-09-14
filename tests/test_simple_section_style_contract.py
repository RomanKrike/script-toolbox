# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_simple_section_reuses_runtime_folder_and_shared_group_box_style():
    runtime = _read("scripts/script_toolbox/ui/runtime.py")
    stylesheet = _read("scripts/script_toolbox/style/stylesheet.py")
    runtime_overrides = _read("scripts/script_toolbox/style/runtime_overrides.py")
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    palette = _read("scripts/script_toolbox/style/palette.py")

    # Simple Section remains Folder renderer chrome, but its persisted mode
    # field name is resolved generically through SectionSpec metadata.
    assert "definition.section_mode(_props(item))" in runtime
    assert "self.folder_type = _section_group_mode(section)" in runtime
    assert 'definition.fields.get("folder_type")' not in runtime
    assert 'elif self.folder_type == "simple":' in runtime
    assert 'self.header = QtGui.QGroupBox(text_type(label))' in runtime
    assert 'self.header.setObjectName("SimpleSectionGroupBox")' in runtime
    assert 'self.header.setProperty("nested", self.is_nested)' in runtime

    assert 'self.content.setObjectName("RuntimeFolderContent")' in runtime
    assert 'content_parent = self.header' in runtime
    assert 'content_host = group_layout' in runtime

    assert 'QGroupBox {' in stylesheet
    assert 'border: 1px solid %(BORDER_GROUP)s;' in stylesheet
    assert 'QGroupBox::title {' in stylesheet
    assert 'subcontrol-origin: margin;' in stylesheet
    assert 'left: 8px;' in stylesheet
    assert 'QGroupBox#SimpleSectionGroupBox::title {' in stylesheet
    assert 'background-color: %(CONTENT_BG)s;' in stylesheet
    assert 'color: %(TEXT_SECTION)s;' in stylesheet
    assert 'font-weight: bold;' in stylesheet
    assert 'QGroupBox#SimpleSectionGroupBox[nested="true"]::title {' in stylesheet
    assert 'background-color: %(SIMPLE_SECTION_NESTED_BG)s;' in stylesheet

    assert 'from .palette import CONTENT_BG' in runtime_overrides
    assert 'from .palette import SIMPLE_SECTION_NESTED_BG' in runtime_overrides
    assert 'background-color: {content_bg};' in runtime_overrides
    assert 'background-color: {simple_section_nested_bg};' in runtime_overrides
    assert 'content_bg=CONTENT_BG' in runtime_overrides
    assert 'simple_section_nested_bg=SIMPLE_SECTION_NESTED_BG' in runtime_overrides
    assert 'palette(window)' not in runtime_overrides

    assert 'SimpleSectionHeader' not in runtime
    assert 'SimpleSectionHeader' not in stylesheet
    assert 'RUNTIME_SIMPLE_HEADER_' not in runtime
    assert 'RUNTIME_SIMPLE_HEADER_' not in metrics

    assert 'BORDER_GROUP = "#414141"' in palette
    assert 'TEXT_SECTION = TEXT_PRIMARY' in palette
    assert 'SIMPLE_SECTION_NESTED_BG = CONTENT_BG' in palette
