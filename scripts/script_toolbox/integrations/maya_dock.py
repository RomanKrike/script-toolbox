# -*- coding: utf-8 -*-
"""Native Maya workspace and legacy dock containers for Script Toolbox."""
from __future__ import print_function

from ..compat import QtCore, QtGui, omui, shiboken
from ..core.logging_utils import get_logger
from ..pycompat import integer_type
from ..ui.debounced_main_window import active_toolbox
from ..ui.panel_container import ScriptToolboxPanel


WORKSPACE_CONTROL = "ScriptToolboxWorkspaceControl"
LEGACY_DOCK = "ScriptToolboxDockControl"
LEGACY_WINDOW = "ScriptToolboxDockContent"
LEGACY_LAYOUT = "ScriptToolboxDockLayout"
RESTORE_SCRIPT = (
    "import script_toolbox.integrations.maya_dock as _st_dock; "
    "_st_dock.restore_workspace_control()"
)
_ATTACH_RETRY_MS = 100
_MAX_ATTACH_ATTEMPTS = 30
_PENDING_ATTACHES = set()


def _cmds():
    import maya.cmds as cmds
    return cmds


def _add_content(control_name):
    if omui is None or shiboken is None:
        raise RuntimeError("Maya Qt control bridge is unavailable.")
    if control_name == LEGACY_LAYOUT:
        pointer = omui.MQtUtil.findLayout(control_name)
    else:
        pointer = omui.MQtUtil.findControl(control_name)
    if not pointer:
        raise RuntimeError("Maya dock content was not found: " + control_name)
    parent = shiboken.wrapInstance(integer_type(pointer), QtGui.QWidget)
    existing = parent.findChild(QtGui.QWidget, "ScriptToolboxPanelContent")
    if existing is not None:
        if parent.isVisible() and hasattr(existing, "ensure_toolbox"):
            existing.ensure_toolbox()
        if parent.isVisible():
            existing.show()
        return existing
    container = ScriptToolboxPanel()
    widget_pointer = shiboken.getCppPointer(container)[0]
    omui.MQtUtil.addWidgetToMayaLayout(
        integer_type(widget_pointer), integer_type(pointer)
    )
    if container.parentWidget() is not None and parent.isVisible():
        container.show()
    return container


def _defer_content(control_name):
    """Retry until Maya has attached and exposed the workspace content."""
    from maya import utils as maya_utils

    if control_name in _PENDING_ATTACHES:
        return
    _PENDING_ATTACHES.add(control_name)

    def add_when_ready(attempt=0):
        try:
            container = _add_content(control_name)
            if hasattr(container, "isVisible") and not container.isVisible():
                parent = container.parentWidget()
                if parent is None or parent.isVisible():
                    raise RuntimeError("Maya ScriptToolbox container is not visible yet.")
        except Exception:
            if attempt + 1 < _MAX_ATTACH_ATTEMPTS:
                QtCore.QTimer.singleShot(
                    _ATTACH_RETRY_MS,
                    lambda: add_when_ready(attempt + 1)
                )
                return
            get_logger().exception(
                "Could not populate Maya ScriptToolbox control %s after %s attempts.",
                control_name, _MAX_ATTACH_ATTEMPTS
            )
        _PENDING_ATTACHES.discard(control_name)

    try:
        maya_utils.executeDeferred(add_when_ready)
    except Exception:
        _PENDING_ATTACHES.discard(control_name)
        raise


def _add_or_defer(control_name):
    _defer_content(control_name)
    try:
        return _add_content(control_name)
    except RuntimeError:
        # findControl may not be ready while Maya creates/restores its layout.
        return None


def restore_workspace_control():
    """Called by Maya's workspace restoration uiScript."""
    return _add_or_defer(WORKSPACE_CONTROL)


def repair_saved_workspace_control():
    """Attach content when Maya restores a saved tab before our menu loads."""
    cmds = _cmds()
    if not hasattr(cmds, "workspaceControl") or not cmds.workspaceControl(
        WORKSPACE_CONTROL, exists=True
    ):
        return False
    cmds.workspaceControl(
        WORKSPACE_CONTROL, edit=True,
        uiScript=RESTORE_SCRIPT,
        loadImmediately=True
    )
    _defer_content(WORKSPACE_CONTROL)
    return True


def _open_workspace_control(cmds):
    if cmds.workspaceControl(WORKSPACE_CONTROL, exists=True):
        cmds.workspaceControl(
            WORKSPACE_CONTROL, edit=True,
            uiScript=RESTORE_SCRIPT,
            loadImmediately=True
        )
        cmds.workspaceControl(WORKSPACE_CONTROL, edit=True, restore=True)
        cmds.workspaceControl(WORKSPACE_CONTROL, edit=True, visible=True)
        return _add_or_defer(WORKSPACE_CONTROL)
    cmds.workspaceControl(
        WORKSPACE_CONTROL,
        label="ScriptToolbox",
        floating=True,
        retain=True,
        duplicatable=False,
        uiScript=RESTORE_SCRIPT,
        loadImmediately=True
    )
    cmds.workspaceControl(WORKSPACE_CONTROL, edit=True, restore=True)
    cmds.workspaceControl(WORKSPACE_CONTROL, edit=True, visible=True)
    return _add_or_defer(WORKSPACE_CONTROL)


def _open_legacy_dock(cmds):
    if cmds.dockControl(LEGACY_DOCK, exists=True):
        cmds.dockControl(LEGACY_DOCK, edit=True, visible=True)
        return _add_or_defer(LEGACY_LAYOUT)
    window = cmds.window(LEGACY_WINDOW, title="ScriptToolbox")
    cmds.columnLayout(LEGACY_LAYOUT, parent=window, adjustableColumn=True)
    _add_or_defer(LEGACY_LAYOUT)
    cmds.dockControl(
        LEGACY_DOCK,
        label="ScriptToolbox",
        content=window,
        area="right",
        floating=True,
        allowedArea=["left", "right"]
    )
    return window


def open_pane_tab():
    toolbox = active_toolbox()
    if toolbox is not None:
        if getattr(toolbox, "_script_toolbox_mode", "window") == "panel":
            toolbox.raise_()
            toolbox.activateWindow()
            return toolbox
    cmds = _cmds()
    if hasattr(cmds, "workspaceControl"):
        return _open_workspace_control(cmds)
    return _open_legacy_dock(cmds)


__all__ = [
    "WORKSPACE_CONTROL", "LEGACY_DOCK", "open_pane_tab",
    "repair_saved_workspace_control", "restore_workspace_control",
]
