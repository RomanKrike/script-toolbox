# -*- coding: utf-8 -*-
from __future__ import print_function

from .base import BaseHost
from .callbacks import EVENT_SELECTION_CHANGED
from .callbacks import HostCallbackGroup
from .callbacks import HostCallbackHandle
from .standalone_host import StandaloneHost


def _import_host_module(name):
    """Skip only an absent top-level host, never an import failure inside it."""
    import importlib
    import pkgutil
    import sys

    root = name.split(".", 1)[0]
    # get_loader is available on Python 2.7. Looking up a top-level module
    # does not execute its initializer; importing a present host is separate.
    if root not in sys.modules and pkgutil.get_loader(root) is None:
        return None
    return importlib.import_module(name)


def _detect_host():
    import os
    if os.environ.get("SCRIPT_TOOLBOX_DISCOVERY_WORKER") == "1":
        # The read-only discovery subprocess must never import a host API.
        return StandaloneHost()
    import importlib
    for host_module, adapter_module, class_name in (
        ("maya.cmds", ".maya_host", "MayaHost"),
        ("nuke", ".nuke_host", "NukeHost"),
        ("hou", ".houdini_host", "HoudiniHost"),
    ):
        module = _import_host_module(host_module)
        if module is None:
            continue
        if host_module == "nuke" and not hasattr(module, "selectedNodes"):
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
