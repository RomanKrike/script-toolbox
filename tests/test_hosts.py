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
