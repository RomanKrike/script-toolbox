# -*- coding: utf-8 -*-
from __future__ import print_function

import importlib
import sys
import types

from script_toolbox.hosts.callbacks import EVENT_SELECTION_CHANGED


class FakeNode(object):

    def __init__(
        self,
        name,
        path
    ):
        self._name = name
        self._path = path
        self.selected = False

    def name(self):
        return self._name

    def path(self):
        return self._path

    def setSelected(
        self,
        value,
        clear_all_selected=False
    ):
        self.selected = bool(
            value
        )


class FakeUi(object):

    def __init__(self):
        self.selection_callbacks = []

    def addSelectionCallback(
        self,
        callback
    ):
        self.selection_callbacks.append(
            callback
        )

    def removeSelectionCallback(
        self,
        callback
    ):
        self.selection_callbacks.remove(
            callback
        )


def _fake_hou(
    monkeypatch
):
    node_a = FakeNode(
        "geo1",
        "/obj/geo1"
    )
    node_b = FakeNode(
        "cam1",
        "/obj/cam1"
    )

    module = types.ModuleType(
        "hou"
    )
    module.ui = FakeUi()
    module.applicationVersionString = lambda: "19.0.720"
    module.selectedNodes = lambda: [
        node_a,
        node_b,
    ]

    nodes = {
        node_a.path(): node_a,
        node_b.path(): node_b,
    }

    module.node = lambda path: nodes.get(
        path
    )

    def _clear_all_selected():
        for node in nodes.values():
            node.selected = False

    module.clearAllSelected = _clear_all_selected
    module.hscript = lambda code: (
        "stdout:{0}".format(
            code
        ),
        "",
    )
    module.getenv = lambda name: (
        "/tmp/houdini19.0"
        if name == "HOUDINI_USER_PREF_DIR"
        else None
    )

    monkeypatch.setitem(
        sys.modules,
        "hou",
        module
    )

    return (
        module,
        node_a,
        node_b,
    )


def test_houdini_host_adapter_with_fake_hou(
    monkeypatch
):
    fake_hou, node_a, node_b = _fake_hou(
        monkeypatch
    )

    sys.modules.pop(
        "script_toolbox.hosts.houdini_host",
        None
    )

    module = importlib.import_module(
        "script_toolbox.hosts.houdini_host"
    )
    host = module.HoudiniHost()

    assert host.app_version() == "19.0.720"
    assert host.current_selection(
        long_names=True
    ) == [
        "/obj/geo1",
        "/obj/cam1",
    ]
    assert host.current_selection(
        long_names=False
    ) == [
        "geo1",
        "cam1",
    ]
    assert host.object_exists(
        "/obj/geo1"
    ) is True
    assert host.object_exists(
        "/obj/missing"
    ) is False
    assert host.available_languages() == (
        "python",
        "hscript",
    )

    namespace = host.script_namespace()

    assert namespace[
        "hou"
    ] is fake_hou

    assert host.select_objects(
        [
            "/obj/cam1",
        ]
    ) is True
    assert node_a.selected is False
    assert node_b.selected is True

    result = host.execute_native(
        "hscript",
        "echo hello"
    )

    assert result == (
        "stdout:echo hello",
        "",
    )
    assert host.user_config_dir() == "/tmp/houdini19.0"


def test_houdini_selection_callback_contract(
    monkeypatch
):
    fake_hou, node_a, _node_b = _fake_hou(
        monkeypatch
    )

    sys.modules.pop(
        "script_toolbox.hosts.houdini_host",
        None
    )

    module = importlib.import_module(
        "script_toolbox.hosts.houdini_host"
    )
    host = module.HoudiniHost()
    calls = []

    assert host.supports_callback(
        EVENT_SELECTION_CHANGED
    ) is True

    handle = host.add_callback(
        EVENT_SELECTION_CHANGED,
        lambda: calls.append(
            "changed"
        )
    )

    assert handle is not None
    assert len(
        fake_hou.ui.selection_callbacks
    ) == 1

    fake_hou.ui.selection_callbacks[0](
        [
            node_a,
        ]
    )

    assert calls == [
        "changed",
    ]
    assert handle.close() is True
    assert fake_hou.ui.selection_callbacks == []


class FakeHoudiniHost(object):

    key = "houdini"
    display_name = "Houdini"

    def shift_pressed_native(self):
        return None


def test_houdini_compat_uses_houdini_qt_main_window(
    monkeypatch
):
    import script_toolbox.hosts as hosts_module

    marker = object()
    fake_hou = types.ModuleType(
        "hou"
    )

    class FakeQtApi(object):

        @staticmethod
        def mainWindow():
            return marker

    fake_hou.qt = FakeQtApi()
    fake_hou.ui = FakeUi()

    fake_pyside = types.ModuleType(
        "PySide2"
    )
    fake_qt_core = types.ModuleType(
        "PySide2.QtCore"
    )
    fake_qt_gui = types.ModuleType(
        "PySide2.QtGui"
    )
    fake_qt_widgets = types.ModuleType(
        "PySide2.QtWidgets"
    )

    class FakeApplication(object):

        @staticmethod
        def keyboardModifiers():
            return 0

    class FakeQt(object):
        ShiftModifier = 1

    fake_qt_widgets.QApplication = FakeApplication
    fake_qt_core.Qt = FakeQt
    fake_pyside.QtCore = fake_qt_core
    fake_pyside.QtGui = fake_qt_gui
    fake_pyside.QtWidgets = fake_qt_widgets

    monkeypatch.setattr(
        hosts_module,
        "HOST",
        FakeHoudiniHost()
    )
    monkeypatch.setitem(
        sys.modules,
        "hou",
        fake_hou
    )
    monkeypatch.setitem(
        sys.modules,
        "PySide2",
        fake_pyside
    )
    monkeypatch.setitem(
        sys.modules,
        "PySide2.QtCore",
        fake_qt_core
    )
    monkeypatch.setitem(
        sys.modules,
        "PySide2.QtGui",
        fake_qt_gui
    )
    monkeypatch.setitem(
        sys.modules,
        "PySide2.QtWidgets",
        fake_qt_widgets
    )
    monkeypatch.setitem(
        sys.modules,
        "shiboken2",
        types.ModuleType(
            "shiboken2"
        )
    )

    sys.modules.pop(
        "script_toolbox.compat",
        None
    )

    try:
        compat = importlib.import_module(
            "script_toolbox.compat"
        )

        assert compat.HOST_KEY == "houdini"
        assert compat.hou is fake_hou
        assert compat.main_window() is marker
        assert compat.QtGui.QApplication is FakeApplication
    finally:
        sys.modules.pop(
            "script_toolbox.compat",
            None
        )
