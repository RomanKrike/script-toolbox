# -*- coding: utf-8 -*-
from __future__ import print_function

import sys

try:
    reload
except NameError:
    from importlib import reload


def show():
    from .ui.main_window import show as _show
    return _show()


def reload_toolbox():
    """
    Development reload for Maya 2015.

    Close the live window first, then reload child modules from deepest names
    to shallowest names so UI classes do not keep stale module references.
    """
    try:
        from .ui.main_window import close_toolbox
        close_toolbox()
    except Exception:
        pass

    prefix = "script_toolbox."

    names = [
        name
        for name in list(sys.modules.keys())
        if (
            name.startswith(prefix) and
            name != __name__
        )
    ]

    names.sort(
        key=lambda value: (
            value.count("."),
            len(value)
        ),
        reverse=True
    )

    for name in names:
        module = sys.modules.get(
            name
        )

        if module is None:
            continue

        try:
            reload(
                module
            )
        except Exception:
            pass

    return show()
