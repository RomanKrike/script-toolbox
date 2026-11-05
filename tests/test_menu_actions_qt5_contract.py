"""Menu actions work with bindings that expose only QWidget.addAction(QAction)."""
import importlib.util
import os
import sys
from types import ModuleType, SimpleNamespace


def test_menu_action_uses_explicit_qaction_for_qt5(monkeypatch):
    class Action(object):
        def __init__(self, text, parent):
            self.text = text
            self.parent = parent

    class Menu(object):
        def __init__(self):
            self.actions = []

        def addAction(self, action):
            if not isinstance(action, Action):
                raise TypeError("QWidget.addAction(QAction) expected")
            self.actions.append(action)

    fake_compat = ModuleType("script_toolbox.compat")
    fake_compat.QtGui = SimpleNamespace(QAction=Action)
    monkeypatch.setitem(sys.modules, "script_toolbox.compat", fake_compat)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "scripts", "script_toolbox", "ui", "menu_actions.py")
    spec = importlib.util.spec_from_file_location("script_toolbox.ui.menu_actions", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    menu = Menu()
    action = module.add_menu_action(menu, "Open Editor")
    assert action is menu.actions[0]
    assert action.text == "Open Editor"
    assert action.parent is menu
