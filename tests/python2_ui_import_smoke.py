# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import types


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import script_toolbox


class _DummyMeta(type):
    def __getattr__(cls, name):
        return 0


class _DummyBase(object):
    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return _DummyQtObject()

    def __call__(self, *args, **kwargs):
        return _DummyQtObject()

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0

    def __bool__(self):
        return False

    def __nonzero__(self):
        return False

    def __int__(self):
        return 0

    def __index__(self):
        return 0

    def __or__(self, other):
        return 0

    def __and__(self, other):
        return 0


_DummyQtObject = _DummyMeta(
    "_DummyQtObject",
    (_DummyBase,),
    {}
)


class _QtNamespace(object):
    def __getattr__(self, name):
        return _DummyQtObject


class _Host(object):
    key = "maya"
    display_name = "Maya"
    native_script_language = "mel"

    def app_version(self):
        return "2015"

    def __getattr__(self, name):
        def callback(*args, **kwargs):
            return None
        return callback


try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


compat = types.ModuleType("script_toolbox.compat")
compat.HOST = _Host()
compat.QtCore = _QtNamespace()
compat.QtGui = _QtNamespace()
compat.StringIO = StringIO
compat.main_window = lambda: None
sys.modules["script_toolbox.compat"] = compat

# Match the production entry path: import the runtime window from a cold
# script_toolbox.ui package. This exercises ui/__init__.py, ui/bootstrap.py,
# the Inspector registry and debounced_main_window under Python 2.7 import
# semantics without requiring Maya/PySide binaries on CI.
from script_toolbox.ui.debounced_main_window import ScriptToolbox
import script_toolbox.ui as ui
from script_toolbox.ui import properties


assert ScriptToolbox is not None
assert ui.InterfaceEditor is not None
assert ui.ScriptToolbox is not None
assert not hasattr(properties, "PROPERTY_EDITORS")

print("Python 2 full UI import smoke passed.")
