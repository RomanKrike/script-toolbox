# -*- coding: utf-8 -*-
"""Palette-colored checkbox marks, readable by Qt4 without QtSvg.

QSS images need file URLs. Keep these tiny XPMs for the process lifetime;
creating them does not require a QApplication or a writable installation.
"""
import atexit
import os
import shutil
import tempfile

from . import palette


_CHECK = (
    "            ",
    "            ",
    "         XX ",
    "        XXX ",
    "       XXX  ",
    " XX   XXX   ",
    " XXX XXX    ",
    "  XXXXX     ",
    "   XXX      ",
    "    X       ",
    "            ",
    "            ",
)
_MIXED = tuple("  XXXXXXXX  " if 5 <= y <= 6 else "            "
               for y in range(12))
_DIRECTORY = tempfile.mkdtemp(prefix="script-toolbox-checkbox-")
atexit.register(shutil.rmtree, _DIRECTORY, ignore_errors=True)


def _write_mark(name, rows, color):
    path = os.path.join(_DIRECTORY, name + ".xpm")
    lines = ["12 12 2 1", "  c None", "X c " + color] + list(rows)
    with open(path, "w") as handle:
        handle.write("/* XPM */\nstatic const char *mark[] = {\n")
        handle.write(",\n".join('"' + line + '"' for line in lines))
        handle.write("\n};\n")
    return path.replace("\\", "/")


MARK_IMAGES = {}
for _state, _rows in (("checked", _CHECK), ("indeterminate", _MIXED)):
    for _disabled in (False, True):
        _name = _state + ("_disabled" if _disabled else "")
        _color = palette.TEXT_DISABLED if _disabled else palette.TEXT_ON_ACCENT
        MARK_IMAGES[_name] = _write_mark(_name, _rows, _color)
