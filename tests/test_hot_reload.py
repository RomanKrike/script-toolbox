# -*- coding: utf-8 -*-

from script_toolbox.bootstrap import package_child_module_names


def test_package_child_module_names_excludes_root():
    names = package_child_module_names([
        "sys",
        "script_toolbox",
        "script_toolbox.constants",
        "script_toolbox.ui",
        "script_toolbox.ui.main_window",
    ])

    assert "script_toolbox" not in names
    assert "script_toolbox.constants" in names
    assert "script_toolbox.ui.main_window" in names


def test_package_child_module_names_ignores_other_packages():
    names = package_child_module_names([
        "script_toolbox.core.updater",
        "other_package.script_toolbox",
        "script_toolbox_extra",
    ])

    assert names == [
        "script_toolbox.core.updater",
    ]


def test_package_child_module_names_are_deepest_first():
    names = package_child_module_names([
        "script_toolbox.ui",
        "script_toolbox.ui.properties",
        "script_toolbox.ui.properties.button",
        "script_toolbox.core",
    ])

    assert names.index(
        "script_toolbox.ui.properties.button"
    ) < names.index(
        "script_toolbox.ui.properties"
    )

    assert names.index(
        "script_toolbox.ui.properties"
    ) < names.index(
        "script_toolbox.ui"
    )
