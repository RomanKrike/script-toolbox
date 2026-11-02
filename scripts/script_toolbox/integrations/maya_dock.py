# -*- coding: utf-8 -*-
"""Native Maya workspace and legacy dock containers for Script Toolbox."""
from __future__ import print_function

from ..compat import QtGui, omui, shiboken
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
        if hasattr(existing, "ensure_toolbox"):
            existing.ensure_toolbox()
        return existing
    container = ScriptToolboxPanel()
    widget_pointer = shiboken.getCppPointer(container)[0]
    omui.MQtUtil.addWidgetToMayaLayout(
        integer_type(widget_pointer), integer_type(pointer)
    )
    return container


def _defer_content(control_name):
    """Let Maya finish building/restoring the control before filling it."""
    from maya import utils as maya_utils

    def add_when_ready():
        try:
            _add_content(control_name)
        except Exception:
            get_logger().exception(
                "Could not populate Maya ScriptToolbox control %s.",
                control_name
            )

    maya_utils.executeDeferred(add_when_ready)


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


def _open_workspace_control(cmds):
    if cmds.workspaceControl(WORKSPACE_CONTROL, exists=True):
        cmds.workspaceControl(WORKSPACE_CONTROL, edit=True, restore=True)
        cmds.workspaceControl(WORKSPACE_CONTROL, edit=True, visible=True)
        return _add_or_defer(WORKSPACE_CONTROL)
    cmds.workspaceControl(
        WORKSPACE_CONTROL,
        label="ScriptToolbox",
        floating=True,
        retain=True,
        duplicatable=False,
        uiScript=RESTORE_SCRIPT
    )
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
    "restore_workspace_control",
]
