"""Contract for the script embedded in Houdini's Python Panel interface."""
import sys
from types import ModuleType
from xml.etree import ElementTree

from script_toolbox.integrations.houdini import HoudiniAdapter


def test_panel_creation_error_is_visible_and_destroy_is_safe(monkeypatch):
    script = ElementTree.fromstring(HoudiniAdapter._panel_content()).find(
        ".//script"
    ).text

    panel_module = ModuleType("script_toolbox.ui.panel_container")

    class BrokenPanel(object):
        def __init__(self):
            raise RuntimeError("pane construction failed")

    panel_module.ScriptToolboxPanel = BrokenPanel
    monkeypatch.setitem(sys.modules, panel_module.__name__, panel_module)

    class Label(object):
        def __init__(self, message):
            self.message = message

        def setWordWrap(self, value):
            self.word_wrap = value

    hutil = ModuleType("hutil")
    hutil.__path__ = []
    hutil_qt = ModuleType("hutil.Qt")
    hutil_qt.QtWidgets = type("Widgets", (), {"QLabel": Label})
    monkeypatch.setitem(sys.modules, "hutil", hutil)
    monkeypatch.setitem(sys.modules, "hutil.Qt", hutil_qt)

    runtime_module = ModuleType("script_toolbox.ui.debounced_main_window")
    runtime_module.active_toolbox = lambda: None
    monkeypatch.setitem(sys.modules, runtime_module.__name__, runtime_module)

    namespace = {}
    exec(compile(script, "script_toolbox.pypanel", "exec"), namespace)
    label = namespace["onCreateInterface"]()
    assert label.message.endswith("pane construction failed")
    assert label.word_wrap is True
    namespace["onDestroyInterface"]()
