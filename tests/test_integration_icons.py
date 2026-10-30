# -*- coding: utf-8 -*-

import importlib.util
import os
import struct
import sys
import types
import xml.etree.ElementTree as ET

from script_toolbox.integrations.base import DccInstallation
from script_toolbox.integrations.base import STATUS_INSTALLED
from script_toolbox.integrations.base import STATUS_UPDATE_REQUIRED
from script_toolbox.integrations.houdini import HoudiniAdapter
from script_toolbox.integrations.icons import integration_icon_path
from script_toolbox.integrations.icons import maya_shelf_icon_path
from script_toolbox.integrations.maya import MayaAdapter
from script_toolbox.integrations.maya import _shelf_content


def test_integration_icon_is_a_packaged_png_without_qt():
    path = integration_icon_path()
    assert os.path.isabs(path)
    assert "\\" not in path
    with open(path, "rb") as handle:
        assert handle.read(8) == b"\x89PNG\r\n\x1a\n"


def test_generated_shelves_escape_icon_paths(tmp_path):
    root = str(tmp_path / 'Toolbox & "Studio" / Скрипты')
    icon = integration_icon_path(root)
    maya_shelf = _shelf_content(root)
    assert '-width 34' in maya_shelf
    assert '-height 34' in maya_shelf
    assert '-image1 "' + maya_shelf_icon_path(root).replace('"', '\\"') + '"' in maya_shelf
    assert 'pythonFamily.png' not in maya_shelf
    houdini = HoudiniAdapter(distribution_path=root, user_root=str(tmp_path))
    tool = ET.fromstring(houdini._shelf_content()).find("tool")
    assert tool.get("icon") == icon
    assert tool.find("script").text.strip().endswith("script_toolbox.show()")


def test_maya_repair_upgrades_the_old_python_shelf_icon(tmp_path):
    user_root = tmp_path / "maya"
    (user_root / "2026").mkdir(parents=True)
    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "Toolbox With Spaces"),
        user_root=str(user_root),
        registry_reader=lambda: [("2026", str(tmp_path / "Maya2026"))],
        config_path=str(tmp_path / "dcc.json")
    )
    target = next(item for item in adapter.get_installations()
                  if item.version == "2026")
    assert adapter.install(target).state == STATUS_INSTALLED
    shelf_path = adapter._shelf_path(target)
    with open(shelf_path, "r", encoding="utf-8") as handle:
        shelf = handle.read()
    old_shelf = shelf.replace(
        maya_shelf_icon_path(adapter.distribution_path), "pythonFamily.png"
    )
    with open(shelf_path, "w", encoding="utf-8") as handle:
        handle.write(old_shelf)
    assert adapter.status(target).state == STATUS_UPDATE_REQUIRED
    assert adapter.repair(target).state == STATUS_INSTALLED
    with open(shelf_path, "r", encoding="utf-8") as handle:
        repaired = handle.read()
    assert "pythonFamily.png" not in repaired
    assert maya_shelf_icon_path(adapter.distribution_path) in repaired
    assert repaired.count("ScriptToolboxOpenButton") == 1


def test_houdini_repair_upgrades_the_old_python_shelf_icon(tmp_path):
    adapter = HoudiniAdapter(
        distribution_path=str(tmp_path / "Toolbox & Studio"),
        user_root=str(tmp_path), config_path=str(tmp_path / "dcc.json")
    )
    target = DccInstallation(
        dcc="houdini", display_name="Houdini", version="21.0",
        user_config_path=str(tmp_path / "houdini21.0"),
        integration_available=True, supported=True
    )
    assert adapter.install(target).state == STATUS_INSTALLED
    shelf_path = adapter._shelf_path(target)
    root = ET.fromstring(adapter._shelf_content())
    root.find("tool").set("icon", "PYTHON")
    ET.ElementTree(root).write(shelf_path, encoding="utf-8", xml_declaration=True)
    assert adapter.status(target).state == STATUS_UPDATE_REQUIRED
    assert adapter.repair(target).state == STATUS_INSTALLED
    assert ET.parse(shelf_path).find("tool").get("icon") == (
        integration_icon_path(adapter.distribution_path)
    )


def test_maya_live_shelf_and_menu_use_the_shared_icon(monkeypatch):
    from script_toolbox.integrations import maya_runtime
    buttons, menu_items = [], []
    fake = types.SimpleNamespace(
        shelfLayout=lambda *a, **kw: True,
        shelfButton=lambda *a, **kw: buttons.append(kw) or "button",
        menu=lambda *a, **kw: "menu",
        menuItem=lambda **kw: menu_items.append(kw)
    )
    monkeypatch.setattr(maya_runtime, "_cmds", lambda: fake)
    monkeypatch.setattr(maya_runtime, "_shelf_parent", lambda: "ShelfLayout")
    monkeypatch.setattr(maya_runtime, "remove_shelf_button", lambda: False)
    monkeypatch.setattr(maya_runtime, "remove_main_menu", lambda: False)
    maya_runtime.ensure_shelf_button()
    maya_runtime.ensure_main_menu()
    assert buttons[0]["image1"] == maya_shelf_icon_path()
    assert buttons[0]["width"] == buttons[0]["height"] == 34
    assert buttons[0]["style"] == "iconOnly"
    opener = next(item for item in menu_items
                  if item.get("label") == "Open ScriptToolbox")
    assert opener["image"] == integration_icon_path()
    assert buttons[0]["command"] == "import script_toolbox; script_toolbox.show()"
    assert buttons[0]["sourceType"] == "python"
    assert buttons[0]["docTag"] == "ScriptToolbox/launcher"
    assert callable(opener["command"])


def test_nuke_registration_refreshes_icons_without_duplicate_commands(monkeypatch):
    class Menu(object):
        def __init__(self):
            self.items = {}
            self.icon_path = "old.png"
            self.script = None

        def findItem(self, name):
            return self.items.get(name)

        def addMenu(self, name, icon=None):
            item = self.items[name] = Menu()
            item.icon_path = icon
            return item

        def addCommand(self, name, script, icon=None):
            item = self.items[name] = Menu()
            item.script = script
            item.icon_path = icon
            return item

        def setIcon(self, icon):
            self.icon_path = icon

    root = Menu()
    fake_nuke = types.SimpleNamespace(menu=lambda name: root)
    compat = types.SimpleNamespace(
        HOST=types.SimpleNamespace(key="nuke"), nuke=fake_nuke,
        nukescripts=None
    )
    monkeypatch.setitem(sys.modules, "script_toolbox.compat", compat)
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "scripts", "script_toolbox", "nuke_integration.py")
    spec = importlib.util.spec_from_file_location("script_toolbox.nuke_integration", path)
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    first = runtime.register_menu()
    opener = first.findItem("Open")
    first.icon_path = opener.icon_path = "old.png"
    assert runtime.register_menu() is first
    assert first.findItem("Open") is opener
    assert len(root.items) == 1
    assert set(first.items) == {"Open", "Open Pane Tab"}
    assert first.icon_path == opener.icon_path == integration_icon_path()
    assert opener.script == "import script_toolbox; script_toolbox.show()"


def test_maya_shelf_image_has_native_icon_dimensions():
    with open(maya_shelf_icon_path(), "rb") as handle:
        header = handle.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", header[16:24]) == (32, 32)
