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


def test_runtime_scroll_is_wrapped_by_external_pane_frame():
    source = _read(
        "scripts/script_toolbox/ui/runtime_pane.py"
    )

    assert 'pane.setObjectName("RuntimePane")' in source
    assert "root.removeWidget(scroll)" in source
    assert "scroll.setParent(pane)" in source
    assert "pane_layout.addWidget(scroll)" in source
    assert "root.insertWidget(index, pane" in source


def test_runtime_pane_matches_editor_pane_visual_contract():
    runtime_style = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )
    base_style = _read(
        "scripts/script_toolbox/style/stylesheet.py"
    )

    editor_rule = base_style.split(
        "QWidget#EditorPane {",
        1
    )[1].split("}", 1)[0]
    runtime_rule = runtime_style.split(
        "QFrame#RuntimePane {",
        1
    )[1].split("}", 1)[0]

    for token in (
        "background-color: #303030;",
        "border: 1px solid #1b1b1b;",
        "border-radius: 3px;",
    ):
        assert token in editor_rule
        assert token in runtime_rule


def test_runtime_pane_keeps_toolbox_scroll_frameless():
    style = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )
    rule = style.split(
        "QFrame#RuntimePane QScrollArea#ToolboxScroll {",
        1
    )[1].split("}", 1)[0]

    assert "border: 0px;" in rule


def test_ui_installs_runtime_pane_wrapper():
    source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "from .runtime_pane import install_runtime_pane" in source
    assert "install_runtime_pane(\n    ScriptToolbox\n)" in source
