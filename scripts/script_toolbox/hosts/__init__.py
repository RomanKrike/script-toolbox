# -*- coding: utf-8 -*-
from __future__ import print_function

from .base import BaseHost


def _detect_host():
    try:
        from .maya import MayaHost
        return MayaHost()
    except Exception:
        pass

    try:
        from .nuke import NukeHost
        return NukeHost()
    except Exception:
        pass

    return BaseHost()


HOST = _detect_host()


def get_host():
    return HOST


__all__ = [
    "HOST",
    "get_host",
]
