# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(
        ROOT,
        *relative_path.split("/")
    )
    with open(path, "r") as handle:
        return handle.read()


def _rule(source, selector):
    return source.split(
        selector + " {",
        1
    )[1].split("}", 1)[0]


def test_runtime_folder_uses_editor_pane_visual_contract():
    base_style = _read(
        "scripts/script_toolbox/style/stylesheet.py"
    )
    runtime_style = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )

    editor_rule = _rule(
        base_style,
        "QWidget#EditorPane"
    )

    for token in (
        "background-color: #303030;",
        "border: 1px solid #1b1b1b;",
        "border-radius: 3px;",
    ):
        assert token in editor_rule
        assert token in runtime_style

    assert 'QFrame#RuntimeFolder[folderType="collapsible"]' in runtime_style
    assert 'QFrame#RuntimeFolder[folderType="collapsible"][nested="true"]' in runtime_style


def test_runtime_folder_header_reads_as_pane_title_not_separate_card():
    runtime_style = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )

    assert "QPushButton#RuntimeFolderHeader" in runtime_style
    assert "background-color: transparent;" in runtime_style
    assert "color: #e0e0e0;" in runtime_style
    assert "font-weight: bold;" in runtime_style
    assert "text-align: left;" in runtime_style


def test_runtime_folder_style_does_not_restore_whole_toolbox_frame():
    runtime_style = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )

    assert "RuntimePane" not in runtime_style
    assert "RuntimePaneHost" not in runtime_style
