# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_simple_section_reuses_runtime_folder_and_shared_group_box_style():
    runtime = _read("scripts/script_toolbox/ui/runtime.py")
    stylesheet = _read("scripts/script_toolbox/style/stylesheet.py")
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    palette = _read("scripts/script_toolbox/style/palette.py")

    # Simple Section remains the existing RuntimeFolder/simple model. QGroupBox
    # is only runtime chrome, not a new serialized item or container type.
    assert 'self.folder_type = section.get("folder_type", "collapsible")' in runtime
    assert 'elif self.folder_type == "simple":' in runtime
    assert 'self.header = QtGui.QGroupBox(text_type(label))' in runtime
    assert 'self.header.setObjectName("SimpleSectionGroupBox")' in runtime
    assert 'self.header.setProperty("nested", self.is_nested)' in runtime

    # Content remains RuntimeFolderContent so nested-folder detection and all
    # existing runtime child rendering continue to use the same architecture.
    assert 'self.content.setObjectName("RuntimeFolderContent")' in runtime
    assert 'content_parent = self.header' in runtime
    assert 'content_host = group_layout' in runtime

    # The shared QGroupBox contract owns border geometry. Simple Section only
    # overrides title surface/text so the title masks the border beneath it.
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

    # The failed header-frame approach must not survive alongside QGroupBox,
    # otherwise nested/top-level sections can regain a second outline.
    assert 'SimpleSectionHeader' not in runtime
    assert 'SimpleSectionHeader' not in stylesheet
    assert 'RUNTIME_SIMPLE_HEADER_' not in runtime
    assert 'RUNTIME_SIMPLE_HEADER_' not in metrics

    # No new color source is introduced for this fix.
    assert 'BORDER_GROUP = "#414141"' in palette
    assert 'TEXT_SECTION = TEXT_PRIMARY' in palette
    assert 'SIMPLE_SECTION_NESTED_BG = PANEL_BG' in palette
