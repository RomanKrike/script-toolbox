# -*- coding: utf-8 -*-
from __future__ import print_function

from .constants import PLUGIN_VERSION
from .hosts import HOST

__version__ = PLUGIN_VERSION
__host__ = HOST.key


def show():
    from .bootstrap import show as _show
    return _show()


def reload_toolbox():
    from .bootstrap import reload_toolbox as _reload_toolbox
    return _reload_toolbox()


def hot_reload_toolbox():
    from .bootstrap import hot_reload_toolbox as _hot_reload_toolbox
    return _hot_reload_toolbox()


def register_nuke_menu():
    from .nuke_integration import register_menu
    return register_menu()


def register_nuke_panel():
    from .nuke_integration import register_panel
    return register_panel()


def open_pane_tab():
    from .compat import HOST
    if HOST.key == "nuke":
        from .nuke_integration import open_pane_tab as open_panel
    elif HOST.key == "maya":
        from .integrations.maya_dock import open_pane_tab as open_panel
    elif HOST.key == "houdini":
        from .houdini_integration import open_pane_tab as open_panel
    else:
        raise RuntimeError("Pane tabs require Maya, Houdini or Nuke.")
    return open_panel()
