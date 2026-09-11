# -*- coding: utf-8 -*-
from __future__ import print_function

from .base import BaseHost
from .callbacks import EVENT_SELECTION_CHANGED
from .callbacks import HostCallbackGroup
from .callbacks import HostCallbackHandle


def _detect_host():
    try:
        from .maya_host import MayaHost
        return MayaHost()
    except Exception:
        pass

    try:
        from .nuke_host import NukeHost
        return NukeHost()
    except Exception:
        pass

    try:
        from .houdini_host import HoudiniHost
        return HoudiniHost()
    except Exception:
        pass

    return BaseHost()


HOST = _detect_host()


def get_host():
    return HOST


__all__ = [
    "BaseHost",
    "EVENT_SELECTION_CHANGED",
    "HOST",
    "HostCallbackGroup",
    "HostCallbackHandle",
    "get_host",
]
