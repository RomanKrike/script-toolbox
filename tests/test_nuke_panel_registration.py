"""Host API contract without pretending to run a Nuke workspace."""
from types import SimpleNamespace
import importlib.util

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("PySide6") is None,
    reason="Nuke panel registration requires a Qt binding",
)


class FakeMenu(object):
    def __init__(self):
        self.items = {}

    def findItem(self, name):
        return self.items.get(name)

    def addMenu(self, name, **kwargs):
        menu = FakeMenu()
        self.items[name] = menu
        return menu

    def addCommand(self, name, command, **kwargs):
        self.items[name] = SimpleNamespace(setIcon=lambda icon: None, command=command)

    def setIcon(self, icon):
        pass


def test_register_panel_uses_stable_id_and_single_nuke_pane_entry(monkeypatch):
    from script_toolbox import nuke_integration
    calls = []
    root = FakeMenu()
    host = SimpleNamespace(menu=lambda name: root)
    panels = SimpleNamespace(registerWidgetAsPanel=lambda *args: calls.append(args))
    monkeypatch.setattr(nuke_integration, "HOST", SimpleNamespace(key="nuke"))
    monkeypatch.setattr(nuke_integration, "nuke", host)
    monkeypatch.setattr(nuke_integration, "nukescripts", SimpleNamespace(panels=panels))
    monkeypatch.setattr(nuke_integration, "integration_icon_path", lambda: "icon")

    nuke_integration.register_panel()
    nuke_integration.register_panel()
    nuke_integration.register_menu()
    nuke_integration.register_menu()

    assert calls == [(
        "script_toolbox.ui.panel_container.ScriptToolboxPanel",
        "Script Toolbox",
        nuke_integration.PANEL_ID,
    )]
    menu = root.findItem("Script Toolbox")
    assert set(menu.items) == {"Open", "Open Pane Tab"}
