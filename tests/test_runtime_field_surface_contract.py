# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _source(*parts):
    with open(os.path.join(ROOT, *parts), "r") as handle:
        return handle.read()


def test_runtime_field_list_surface_reads_schema_v21_props():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "scroll_surface_frames.py",
    )
    block = source.split("def install_runtime_scroll_frames", 1)[1]
    block = block.split("def install_script_editor_scroll_frames", 1)[0]

    assert 'props = item.get("props", {})' in block
    assert 'props.get("display_mode") == "list"' in block
    assert 'bool(props.get("multiple", True))' in block
    assert 'item.get("display_mode")' not in block
    assert 'item.get("multiple"' not in block
