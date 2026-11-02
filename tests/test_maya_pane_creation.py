"""Maya host API contract for filling a workspace control after creation."""
import importlib.util
import sys
from types import ModuleType

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("PySide6") is None,
    reason="Maya pane module requires a Qt binding",
)


def test_content_is_retried_after_maya_finishes_creating_control(monkeypatch):
    from script_toolbox.integrations import maya_dock

    callbacks = []
    maya = ModuleType("maya")
    maya.utils = ModuleType("maya.utils")
    maya.utils.executeDeferred = callbacks.append
    monkeypatch.setitem(sys.modules, "maya", maya)
    monkeypatch.setitem(sys.modules, "maya.utils", maya.utils)

    attempts = []

    def add_content(control_name):
        attempts.append(control_name)
        if len(attempts) == 1:
            raise RuntimeError("Maya dock content was not found")
        return "populated"

    monkeypatch.setattr(maya_dock, "_add_content", add_content)
    assert maya_dock.restore_workspace_control() is None
    assert len(callbacks) == 1
    callbacks.pop()()
    assert attempts == [maya_dock.WORKSPACE_CONTROL] * 2


def test_existing_control_is_checked_again_after_restore(monkeypatch):
    from script_toolbox.integrations import maya_dock

    callbacks = []
    maya = ModuleType("maya")
    maya.utils = ModuleType("maya.utils")
    maya.utils.executeDeferred = callbacks.append
    monkeypatch.setitem(sys.modules, "maya", maya)
    monkeypatch.setitem(sys.modules, "maya.utils", maya.utils)

    calls = []
    monkeypatch.setattr(maya_dock, "_add_content", lambda name: calls.append(name))
    class Commands(object):
        def workspaceControl(self, name, **kwargs):
            return kwargs.get("exists", False)

    maya_dock._open_workspace_control(Commands())
    assert calls == [maya_dock.WORKSPACE_CONTROL]
    assert len(callbacks) == 1
    callbacks.pop()()
    assert calls == [maya_dock.WORKSPACE_CONTROL] * 2


def test_workspace_control_loads_ui_script_on_creation_and_restore(monkeypatch):
    from script_toolbox.integrations import maya_dock

    monkeypatch.setattr(maya_dock, "_add_or_defer", lambda name: None)
    calls = []

    class Commands(object):
        exists = False

        def workspaceControl(self, name, **kwargs):
            calls.append(kwargs)
            if kwargs.get("exists"):
                return self.exists

    cmds = Commands()
    maya_dock._open_workspace_control(cmds)
    assert calls[-1]["loadImmediately"] is True
    assert calls[-1]["uiScript"] == maya_dock.RESTORE_SCRIPT

    calls[:] = []
    cmds.exists = True
    maya_dock._open_workspace_control(cmds)
    assert calls[1]["edit"] is True
    assert calls[1]["loadImmediately"] is True
    assert calls[1]["uiScript"] == maya_dock.RESTORE_SCRIPT
