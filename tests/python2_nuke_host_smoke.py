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

    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name

    def fullName(self):
        return self._name


fake_nuke = types.ModuleType(
    "nuke"
)
fake_nuke.NUKE_VERSION_STRING = "12.2v9"
fake_nuke._selection = []
fake_nuke._update_callbacks = []
fake_nuke.selectedNodes = lambda: list(
    fake_nuke._selection
)
fake_nuke.addUpdateUI = lambda callback: (
    fake_nuke._update_callbacks.append(
        callback
    )
)
fake_nuke.removeUpdateUI = lambda callback: (
    fake_nuke._update_callbacks.remove(
        callback
    )
)

fake_nukescripts = types.ModuleType(
    "nukescripts"
)

sys.modules[
    "nuke"
] = fake_nuke
sys.modules[
    "nukescripts"
] = fake_nukescripts


from script_toolbox.hosts.callbacks import EVENT_SELECTION_CHANGED
from script_toolbox.hosts.nuke_host import NukeHost


host = NukeHost()
namespace = host.script_namespace()

assert namespace[
    "nuke"
] is fake_nuke

assert hasattr(
    namespace[
        "nuke"
    ],
    "selectedNodes"
)

assert namespace[
    "nukescripts"
] is fake_nukescripts

assert host.supports_callback(
    EVENT_SELECTION_CHANGED
) is True

received = []
handle = host.add_callback(
    EVENT_SELECTION_CHANGED,
    lambda: received.append(
        tuple(
            host.current_selection(
                long_names=True
            )
        )
    )
)

assert handle is not None
assert len(fake_nuke._update_callbacks) == 1

fake_nuke._update_callbacks[0]()
assert received == []

fake_nuke._selection = [
    FakeNode("Node1")
]
fake_nuke._update_callbacks[0]()
assert received == [
    ("Node1",)
]

fake_nuke._update_callbacks[0]()
assert received == [
    ("Node1",)
]

assert host.remove_callback(
    handle
) is True
assert handle.active is False
assert fake_nuke._update_callbacks == []

print(
    "Python 2 Nuke host import/callback smoke passed."
)
