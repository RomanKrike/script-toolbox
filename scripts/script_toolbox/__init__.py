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
    """Compatibility entry point for existing Nuke startup profiles.

    Dock support has been removed; old menu.py calls now register the normal
    application menu so updating never breaks the user's startup script.
    """
    import warnings
    warnings.warn(
        "Nuke dock panels are no longer supported. Replace "
        "register_nuke_panel() with register_nuke_menu() in menu.py.",
        DeprecationWarning,
        stacklevel=2
    )
    return register_nuke_menu()
