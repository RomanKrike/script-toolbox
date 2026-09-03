# -*- coding: utf-8 -*-
from __future__ import print_function

from .constants import PLUGIN_VERSION

__version__ = PLUGIN_VERSION


def show():
    from .bootstrap import show as _show
    return _show()


def reload_toolbox():
    from .bootstrap import reload_toolbox as _reload_toolbox
    return _reload_toolbox()


def hot_reload_toolbox():
    from .bootstrap import hot_reload_toolbox as _hot_reload_toolbox
    return _hot_reload_toolbox()
