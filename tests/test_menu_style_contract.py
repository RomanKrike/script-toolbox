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


def test_context_menus_keep_visible_group_separators():
    source = _read(
        "scripts/script_toolbox/style/components.py"
    )

    assert "QMenu::separator" in source
    assert "background-color: %(SEPARATOR)s;" in source
    assert "height: 1px;" in source
