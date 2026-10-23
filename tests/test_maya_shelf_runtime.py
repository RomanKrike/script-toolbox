# -*- coding: utf-8 -*-
"""Exercise Maya's rename-on-resave behavior without requiring a Maya process."""

import pytest

from script_toolbox.integrations import maya_runtime
from script_toolbox.integrations.icons import maya_shelf_icon_path
from script_toolbox.integrations.maya_shelf import SHELF_COMMAND, SHELF_DOC_TAG


class ShelfCommands(object):
    def __init__(self, full_children=False):
        self.buttons = {}
        self.shelves = {"ScriptToolbox", "Custom"}
        self.full_children = full_children

    def shelfLayout(self, name, **kwargs):
        if kwargs.get("exists"):
            return name in self.shelves
        if kwargs.get("query"):
            children = [path for path in self.buttons
                        if path.rsplit("|", 1)[0] == name]
            return children if self.full_children else [path.rsplit("|", 1)[1] for path in children]
        self.shelves.add(name)
        return name

    def shelfButton(self, name, **kwargs):
        if kwargs.get("exists"):
            return name in self.buttons
        if kwargs.get("query"):
            flag = next(key for key in kwargs if key != "query")
            return self.buttons[name].get(flag, "")
        path = kwargs.pop("parent") + "|" + name
        assert path not in self.buttons, "Maya may auto-rename a conflicting button"
        self.buttons[path] = kwargs
        return path

    def deleteUI(self, path):
        del self.buttons[path]

    def resave(self):
        for index, path in enumerate(list(self.buttons)):
            if (path.startswith("ScriptToolbox|") and
                    self.buttons[path].get("annotation") == "Open Script Toolbox"):
                self.buttons["ScriptToolbox|shelfButton%d" % index] = self.buttons.pop(path)


def _launcher(command=SHELF_COMMAND, **kwargs):
    result = dict(label="ScriptToolbox", annotation="Open Script Toolbox",
                  command=command, image1="logo_sbt.png", width=1024, height=1024)
    result.update(kwargs)
    return result


@pytest.mark.parametrize("full_children", [False, True])
def test_repeated_startup_repairs_resaved_legacy_duplicates(monkeypatch, full_children):
    cmds = ShelfCommands(full_children)
    cmds.buttons = {
        "ScriptToolbox|shelfButton1": _launcher("<function _open_toolbox at 0xABC123>"),
        "ScriptToolbox|shelfButton2": _launcher("script_toolbox.integrations.maya_runtime._open_toolbox"),
        "ScriptToolbox|shelfButton3": _launcher('python("import script_toolbox; script_toolbox.show()")'),
        "ScriptToolbox|custom": dict(label="ScriptToolbox", command="print('custom')"),
        "Custom|ScriptToolboxOpenButton": _launcher(),
    }
    untouched = {key: value.copy() for key, value in cmds.buttons.items()
                 if key in ("ScriptToolbox|custom", "Custom|ScriptToolboxOpenButton")}
    monkeypatch.setattr(maya_runtime, "_cmds", lambda: cmds)
    monkeypatch.setattr(maya_runtime, "_shelf_parent", lambda: "ShelfLayout")
    for unused in range(3):
        path = maya_runtime.ensure_shelf_button()
        assert len(cmds.buttons) == 3
        button = cmds.buttons[path]
        assert button["command"] == SHELF_COMMAND
        assert button["sourceType"] == "python"
        assert button["docTag"] == SHELF_DOC_TAG
        assert button["image1"] == maya_shelf_icon_path()
        assert button["width"] == button["height"] == 34
        for key, value in untouched.items():
            assert cmds.buttons[key] == value
        cmds.resave()
    assert maya_runtime.remove_shelf_button()
    assert cmds.buttons == untouched
    assert not maya_runtime.remove_shelf_button()


def test_live_callable_button_is_replaced_with_serializable_command(monkeypatch):
    import script_toolbox

    cmds = ShelfCommands()
    cmds.buttons["ScriptToolbox|old"] = _launcher(maya_runtime._open_toolbox)
    monkeypatch.setattr(maya_runtime, "_cmds", lambda: cmds)
    monkeypatch.setattr(maya_runtime, "_shelf_parent", lambda: "ShelfLayout")
    path = maya_runtime.ensure_shelf_button()
    assert list(cmds.buttons) == [path]
    assert cmds.buttons[path]["command"] == SHELF_COMMAND
    calls = []
    monkeypatch.setattr(script_toolbox, "show", lambda: calls.append("opened"))
    exec(cmds.buttons[path]["command"], {})
    assert calls == ["opened"]


def test_custom_double_click_on_a_launcher_is_preserved(monkeypatch):
    cmds = ShelfCommands()
    cmds.buttons["ScriptToolbox|custom"] = _launcher(doubleClickCommand="print('custom')")
    monkeypatch.setattr(maya_runtime, "_cmds", lambda: cmds)
    assert not maya_runtime.remove_shelf_button()
    assert cmds.buttons["ScriptToolbox|custom"]["doubleClickCommand"] == "print('custom')"


def test_removed_shelf_is_not_recreated_when_disabled(monkeypatch):
    cmds = ShelfCommands()
    cmds.shelves.remove("ScriptToolbox")
    monkeypatch.setattr(maya_runtime, "_cmds", lambda: cmds)
    assert not maya_runtime.remove_shelf_button()
    assert "ScriptToolbox" not in cmds.shelves
