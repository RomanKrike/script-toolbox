# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import types


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(
            __file__
        )
    )
)

SCRIPTS = os.path.join(
    ROOT,
    "scripts"
)

if SCRIPTS not in sys.path:
    sys.path.insert(
        0,
        SCRIPTS
    )


class FakeNode(object):

    def __init__(self, path):
        self._path = path
        self.selected = False

    def path(self):
        return self._path

    def name(self):
        return self._path.rsplit("/", 1)[-1]

    def setSelected(self, selected, clear_all_selected=False):
        self.selected = bool(selected)


class FakeUI(object):

    def __init__(self):
        self.callbacks = []

    def addSelectionCallback(self, callback):
        self.callbacks.append(callback)

    def removeSelectionCallback(self, callback):
        self.callbacks.remove(callback)


fake_hou = types.ModuleType("hou")
fake_hou.ui = FakeUI()
fake_hou._selection = []
fake_hou._nodes = {}
fake_hou.applicationVersionString = lambda: "19.5.640"
fake_hou.selectedNodes = lambda: list(fake_hou._selection)
fake_hou.node = lambda path: fake_hou._nodes.get(path)
fake_hou.clearAllSelected = lambda: None
fake_hou.getenv = lambda name: None
fake_hou.hscript = lambda code: ("ok", "")

sys.modules["hou"] = fake_hou


from script_toolbox.hosts.callbacks import EVENT_SELECTION_CHANGED
from script_toolbox.hosts.houdini_host import HoudiniHost


host = HoudiniHost()
namespace = host.script_namespace()

assert namespace["hou"] is fake_hou
assert host.available_languages() == ("python", "hscript")
assert host.supports_callback(EVENT_SELECTION_CHANGED) is True

node = FakeNode("/obj/geo1")
fake_hou._nodes[node.path()] = node
fake_hou._selection = [node]

assert host.current_selection(long_names=True) == ["/obj/geo1"]
assert host.current_selection(long_names=False) == ["geo1"]
assert host.object_exists("/obj/geo1") is True
assert host.select_objects(["/obj/geo1"]) is True
assert node.selected is True

received = []
handle = host.add_callback(
    EVENT_SELECTION_CHANGED,
    lambda: received.append(tuple(host.current_selection()))
)
assert handle is not None
assert len(fake_hou.ui.callbacks) == 1

fake_hou.ui.callbacks[0](fake_hou._selection)
assert received == [("/obj/geo1",)]

assert host.remove_callback(handle) is True
assert handle.active is False
assert fake_hou.ui.callbacks == []

assert host.execute_native("hscript", "echo ok") == ("ok", "")

print("Python 2 Houdini host import/callback smoke passed.")
