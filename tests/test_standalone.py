# -*- coding: utf-8 -*-

import subprocess

from script_toolbox.core import executor
from script_toolbox.hosts.standalone_host import StandaloneHost
from script_toolbox.standalone import exec_application
from script_toolbox.standalone import run_standalone


class FakeApplication(object):
    current = None

    def __init__(self, argv):
        self.argv = list(argv)
        self.exec_calls = 0
        FakeApplication.current = self

    @classmethod
    def instance(cls):
        return cls.current

    def exec_(self):
        self.exec_calls += 1
        return 17


def test_standalone_host_is_explicit_safe_base_host():
    host = StandaloneHost()

    assert host.key == "standalone"
    assert host.display_name == "Standalone"
    assert host.available_languages() == (
        "python",
    )
    assert host.current_selection() == []
    assert host.object_exists("anything") is False
    assert host.script_namespace()["host"] is host


def test_run_standalone_owns_application_and_event_loop():
    FakeApplication.current = None
    shown = []

    result = run_standalone(
        FakeApplication,
        lambda: shown.append(True),
        argv=["ScriptToolbox"]
    )

    assert result == 17
    assert shown == [True]
    assert FakeApplication.current.argv == [
        "ScriptToolbox"
    ]
    assert FakeApplication.current.exec_calls == 1


def test_run_standalone_reuses_existing_application_without_second_loop():
    existing = FakeApplication(
        ["existing"]
    )
    shown = []

    result = run_standalone(
        FakeApplication,
        lambda: shown.append(True),
        argv=["ignored"]
    )

    assert result == 0
    assert shown == [True]
    assert FakeApplication.current is existing
    assert existing.exec_calls == 0


def test_exec_application_supports_qt6_exec_name():
    class Qt6Application(object):
        def exec(self):
            return 23

    assert exec_application(
        Qt6Application()
    ) == 23


def test_standalone_python_binding_uses_existing_executor(monkeypatch):
    host = StandaloneHost()

    monkeypatch.setattr(
        executor,
        "HOST",
        host
    )

    result = executor.execute_script_result(
        "assert 41 + 1 == 42",
        notify=False
    )

    assert result.success is True


def test_standalone_python_binding_can_launch_with_standard_subprocess(
    monkeypatch
):
    host = StandaloneHost()
    calls = []

    monkeypatch.setattr(
        executor,
        "HOST",
        host
    )
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda args: calls.append(
            list(
                args
            )
        )
    )

    result = executor.execute_script_result(
        (
            "import subprocess\n"
            "subprocess.Popen(['notepad.exe'])"
        ),
        notify=False
    )

    assert result.success is True
    assert calls == [
        [
            "notepad.exe",
        ]
    ]
