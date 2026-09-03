# -*- coding: utf-8 -*-
from __future__ import print_function

"""
Temporary bootstrap for the modular refactor branch.

The model/config/executor layers are already extracted. Runtime UI and the
interface editor will be moved next. Until that extraction is complete this
module intentionally raises a clear error instead of silently falling back to
the old monolith.
"""

import sys


def show():
    raise RuntimeError(
        "The modular refactor is in progress. "
        "Runtime UI has not been extracted yet."
    )


def reload_toolbox():
    prefix = "script_toolbox."

    names = [
        name
        for name in sys.modules.keys()
        if name.startswith(prefix)
    ]

    names.sort(
        key=len,
        reverse=True
    )

    for name in names:
        module = sys.modules.get(name)

        if module is None:
            continue

        try:
            reload(module)
        except Exception:
            pass

    return show()
