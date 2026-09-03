# -*- coding: utf-8 -*-

import os

from script_toolbox.hosts.base import BaseHost
from script_toolbox.core import config
from script_toolbox.core import executor


class FakeHost(BaseHost):

    key = "fake"
    display_name = "Fake"

    def __init__(self):
        self.native_calls = []

    def current_selection(
        self,
        long_names=True
    ):
        if long_names:
            return [
                "Group.Node"
            ]

        return [
            "Node"
        ]

    def object_exists(
        self,
        name
    ):
        return name in (
            "Node",
            "Group.Node",
        )

    def select_objects(
        self,
        names
    ):
        self.selected = list(
            names
        )
        return True

    def available_languages(self):
        return (
            "python",
            "fake",
        )

    def script_namespace(self):
        return {
            "host": self,
            "dcc_value": 41,
        }

    def execute_native(
        self,
        language,
        code
    ):
        self.native_calls.append(
            (
                language,
                code,
            )
        )
        return "ok"

    def user_config_dir(self):
        return os.path.join(
            "tmp",
            "fake"
        )

    def config_filename(self):
        return "fake_toolbox.json"


def test_base_host_is_safe_standalone():
    host = BaseHost()

    assert host.key == "standalone"
    assert host.available_languages() == (
        "python",
    )
    assert host.current_selection() == []
    assert host.object_exists(
        "anything"
    ) is False


def test_config_path_uses_active_host(
    monkeypatch
):
    host = FakeHost()

    monkeypatch.setattr(
        config,
        "HOST",
        host
    )
    monkeypatch.delenv(
        "SCRIPT_TOOLBOX_CONFIG_PATH",
        raising=False
    )

    assert config.config_path().endswith(
        os.path.normpath(
            "tmp/fake/fake_toolbox.json"
        )
    )


def test_config_path_environment_override_wins(
    monkeypatch,
    tmp_path
):
    path = str(
        tmp_path /
        "custom.json"
    )

    monkeypatch.setenv(
        "SCRIPT_TOOLBOX_CONFIG_PATH",
        path
    )

    assert config.config_path() == os.path.normpath(
        path
    )


def test_python_executor_uses_host_namespace(
    monkeypatch
):
    host = FakeHost()

    monkeypatch.setattr(
        executor,
        "HOST",
        host
    )

    assert executor.execute_script(
        "assert dcc_value + 1 == 42"
    ) is True


def test_native_executor_routes_to_host(
    monkeypatch
):
    host = FakeHost()

    monkeypatch.setattr(
        executor,
        "HOST",
        host
    )

    assert executor.execute_script(
        "native code",
        language="fake"
    ) is True

    assert host.native_calls == [
        (
            "fake",
            "native code",
        )
    ]


def test_nuke_host_adapter_with_fake_nuke(
    monkeypatch
):
    import importlib
    import sys
    import types

    class FakeNode(object):

        def __init__(
            self,
            name,
            full_name
        ):
            self._name = name
            self._full_name = full_name
            self.selected = True

        def name(self):
            return self._name

        def fullName(self):
            return self._full_name

        def setSelected(
            self,
            value
        ):
            self.selected = bool(
                value
            )

    node_a = FakeNode(
        "Read1",
        "Group1.Read1"
    )
    node_b = FakeNode(
        "Write1",
        "Write1"
    )

    fake_nuke = types.ModuleType(
        "nuke"
    )
    fake_nuke.NUKE_VERSION_STRING = "12.2v9"
    fake_nuke.selectedNodes = lambda: [
        node_a,
        node_b,
    ]
    fake_nuke.toNode = lambda name: {
        "Group1.Read1": node_a,
        "Read1": node_a,
        "Write1": node_b,
    }.get(
        name
    )

    fake_nukescripts = types.ModuleType(
        "nukescripts"
    )

    monkeypatch.setitem(
        sys.modules,
        "nuke",
        fake_nuke
    )
    monkeypatch.setitem(
        sys.modules,
        "nukescripts",
        fake_nukescripts
    )

    sys.modules.pop(
        "script_toolbox.hosts.nuke_host",
        None
    )

    module = importlib.import_module(
        "script_toolbox.hosts.nuke_host"
    )
    host = module.NukeHost()

    assert host.app_version() == "12.2v9"
    assert host.current_selection(
        long_names=True
    ) == [
        "Group1.Read1",
        "Write1",
    ]
    assert host.current_selection(
        long_names=False
    ) == [
        "Read1",
        "Write1",
    ]
    assert host.object_exists(
        "Group1.Read1"
    ) is True
    assert host.object_exists(
        "Missing"
    ) is False
    assert host.available_languages() == (
        "python",
    )

    namespace = host.script_namespace()

    assert namespace[
        "nuke"
    ] is fake_nuke
    assert namespace[
        "nukescripts"
    ] is fake_nukescripts
