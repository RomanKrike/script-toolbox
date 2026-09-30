# -*- coding: utf-8 -*-
from __future__ import print_function

from .base import BaseHost
from .callbacks import EVENT_SELECTION_CHANGED
from .callbacks import HostCallbackGroup
from .callbacks import HostCallbackHandle
from .standalone_host import StandaloneHost


def _detect_host():
    import importlib
    for host_module, adapter_module, class_name in (
        ("maya.cmds", ".maya_host", "MayaHost"),
        ("nuke", ".nuke_host", "NukeHost"),
        ("hou", ".houdini_host", "HoudiniHost"),
    ):
        try:
            module = importlib.import_module(host_module)
            if host_module == "nuke" and not hasattr(module, "selectedNodes"):
                continue
        except ImportError:
            continue
        # A present host with a broken adapter is a startup error; propagating
        # it keeps the real traceback instead of selecting standalone paths.
        adapter = importlib.import_module(adapter_module, __name__)
        return getattr(adapter, class_name)()
    return StandaloneHost()


HOST = _detect_host()


def get_host():
    return HOST


__all__ = [
    "BaseHost",
    "EVENT_SELECTION_CHANGED",
    "HOST",
    "HostCallbackGroup",
    "HostCallbackHandle",
    "StandaloneHost",
    "get_host",
]
