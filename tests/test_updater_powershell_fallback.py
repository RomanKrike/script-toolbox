# -*- coding: utf-8 -*-

import pytest

from script_toolbox.core import updater


def _install_fake_powershell(monkeypatch, process_class):
    monkeypatch.setattr(
        updater,
        "_powershell_executable",
        lambda: "powershell.exe"
    )
    monkeypatch.setattr(
        updater,
        "_hidden_process_kwargs",
        lambda: {}
    )
    monkeypatch.setattr(
        updater.subprocess,
        "Popen",
        process_class
    )


def test_powershell_fallback_avoids_reserved_input_variable(
    monkeypatch,
    tmp_path
):
    destination = str(
        tmp_path / "download.bin"
    )
    captured = {}

    class SuccessfulProcess(object):
        def __init__(self, args, **kwargs):
            captured["args"] = args
            captured["env"] = kwargs.get("env", {})
            self.returncode = 0

        def communicate(self):
            with open(destination, "wb") as handle:
                handle.write(b"ok")
            return b"", b""

    _install_fake_powershell(
        monkeypatch,
        SuccessfulProcess
    )

    result = updater._download_with_powershell(
        "https://example.invalid/archive.zip",
        destination,
        token="test-token",
        timeout=5
    )

    command = captured["args"][-1]

    assert result == destination
    assert "$ErrorActionPreference = 'Stop'" in command
    assert "$responseStream = $response.GetResponseStream()" in command
    assert "$responseStream.Read(" in command
    assert "if ($output -ne $null)" in command
    assert "if ($responseStream -ne $null)" in command
    assert "if ($response -ne $null)" in command
    assert "$input =" not in command
    assert "$input.CopyTo" not in command
    assert "test-token" not in command
    assert captured["env"][
        "SCRIPT_TOOLBOX_UPDATE_TOKEN"
    ] == "test-token"


def test_powershell_fallback_reports_single_network_error(
    monkeypatch,
    tmp_path
):
    destination = str(
        tmp_path / "download.bin"
    )

    class FailedProcess(object):
        def __init__(self, args, **kwargs):
            self.returncode = 1

        def communicate(self):
            return (
                b"",
                b"Unable to connect to the remote server\n"
            )

    _install_fake_powershell(
        monkeypatch,
        FailedProcess
    )

    with pytest.raises(updater.UpdateError) as error:
        updater._download_with_powershell(
            "https://example.invalid/archive.zip",
            destination
        )

    message = str(error.value)

    assert message == (
        "PowerShell download failed: "
        "Unable to connect to the remote server"
    )
    assert "CopyTo" not in message
    assert "null-valued" not in message
    assert "ArrayListEnumeratorSimple" not in message
