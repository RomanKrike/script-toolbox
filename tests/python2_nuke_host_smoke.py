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


fake_nuke = types.ModuleType(
    "nuke"
)
fake_nuke.NUKE_VERSION_STRING = "12.2v9"
fake_nuke.selectedNodes = lambda: []

fake_nukescripts = types.ModuleType(
    "nukescripts"
)

sys.modules[
    "nuke"
] = fake_nuke
sys.modules[
    "nukescripts"
] = fake_nukescripts


from script_toolbox.hosts.nuke import NukeHost


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

print(
    "Python 2 Nuke host import smoke passed."
)
