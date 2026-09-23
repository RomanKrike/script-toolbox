# -*- coding: utf-8 -*-

import pytest

from script_toolbox.core import http_transport


def _reset_preference(monkeypatch, value=False):
    monkeypatch.setattr(
        http_transport,
        "_WINDOWS_POWERSHELL_PREFERRED",
        [bool(value)]
    )


def test_request_bytes_uses_urllib_on_normal_runtime(monkeypatch):
    calls = []
    _reset_preference(monkeypatch)
    monkeypatch.setattr(http_transport, "is_windows", lambda: False)

    def fake_urllib(url, data=None, headers=None, timeout=15, method=None):
        calls.append((url, data, headers, timeout, method))
        return b"ok"

    monkeypatch.setattr(
        http_transport,
        "_urllib_request_bytes",
        fake_urllib
    )

    result = http_transport.request_bytes(
        "https://example.invalid/value",
        headers={"User-Agent": "test"},
        timeout=7
    )

    assert result == b"ok"
    assert calls == [(
        "https://example.invalid/value",
        None,
        {"User-Agent": "test"},
        7,
        None,
    )]


def test_windows_urllib_failure_falls_back_and_remembers(monkeypatch):
    calls = []
    _reset_preference(monkeypatch)
    monkeypatch.setattr(http_transport, "is_windows", lambda: True)
    monkeypatch.setattr(
        http_transport,
        "legacy_windows_python",
        lambda: False
    )

    def fail_urllib(*args, **kwargs):
        calls.append("urllib")
        raise IOError("TLS failure")

    def fake_powershell(*args, **kwargs):
        calls.append("powershell")
        return b"fallback"

    monkeypatch.setattr(
        http_transport,
        "_urllib_request_bytes",
        fail_urllib
    )
    monkeypatch.setattr(
        http_transport,
        "powershell_request",
        fake_powershell
    )

    first = http_transport.request_bytes(
        "https://example.invalid/first"
    )
    second = http_transport.request_bytes(
        "https://example.invalid/second"
    )

    assert first == b"fallback"
    assert second == b"fallback"
    assert calls == ["urllib", "powershell", "powershell"]


def test_legacy_windows_prefers_powershell(monkeypatch):
    calls = []
    _reset_preference(monkeypatch)
    monkeypatch.setattr(http_transport, "is_windows", lambda: True)
    monkeypatch.setattr(
        http_transport,
        "legacy_windows_python",
        lambda: True
    )
    monkeypatch.setattr(
        http_transport,
        "powershell_request",
        lambda *args, **kwargs: calls.append("powershell") or b"ok"
    )
    monkeypatch.setattr(
        http_transport,
        "_urllib_request_bytes",
        lambda *args, **kwargs: calls.append("urllib") or b"urllib"
    )

    assert http_transport.request_bytes(
        "https://example.invalid/value"
    ) == b"ok"
    assert calls == ["powershell"]


def test_powershell_failure_falls_back_to_urllib(monkeypatch):
    calls = []
    _reset_preference(monkeypatch)
    monkeypatch.setattr(http_transport, "is_windows", lambda: True)
    monkeypatch.setattr(
        http_transport,
        "legacy_windows_python",
        lambda: True
    )

    def fail_powershell(*args, **kwargs):
        calls.append("powershell")
        raise http_transport.TransportError("policy blocked")

    def fake_urllib(*args, **kwargs):
        calls.append("urllib")
        return b"urllib"

    monkeypatch.setattr(
        http_transport,
        "powershell_request",
        fail_powershell
    )
    monkeypatch.setattr(
        http_transport,
        "_urllib_request_bytes",
        fake_urllib
    )

    assert http_transport.request_bytes(
        "https://example.invalid/value"
    ) == b"urllib"
    assert calls == ["powershell", "urllib"]


def test_both_transports_fail_with_predictable_error(monkeypatch):
    _reset_preference(monkeypatch)
    monkeypatch.setattr(http_transport, "is_windows", lambda: True)
    monkeypatch.setattr(
        http_transport,
        "legacy_windows_python",
        lambda: False
    )
    monkeypatch.setattr(
        http_transport,
        "_urllib_request_bytes",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            IOError("urllib failed")
        )
    )
    monkeypatch.setattr(
        http_transport,
        "powershell_request",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            http_transport.TransportError("powershell failed")
        )
    )

    with pytest.raises(http_transport.TransportError) as error:
        http_transport.request_bytes(
            "https://example.invalid/value"
        )

    message = str(error.value)
    assert "urllib failed" in message
    assert "powershell failed" in message


def test_non_windows_failure_does_not_try_powershell(monkeypatch):
    calls = []
    _reset_preference(monkeypatch)
    monkeypatch.setattr(http_transport, "is_windows", lambda: False)
    monkeypatch.setattr(
        http_transport,
        "_urllib_request_bytes",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            IOError("offline")
        )
    )
    monkeypatch.setattr(
        http_transport,
        "powershell_request",
        lambda *args, **kwargs: calls.append("powershell")
    )

    with pytest.raises(http_transport.TransportError):
        http_transport.request_bytes(
            "https://example.invalid/value"
        )
    assert calls == []


def test_urllib_download_streams_to_file(monkeypatch, tmp_path):
    destination = str(tmp_path / "download.bin")

    class Response(object):
        def __init__(self):
            self.parts = [b"abc", b"def", b""]
            self.closed = False

        def read(self, size):
            return self.parts.pop(0)

        def close(self):
            self.closed = True

    response = Response()
    monkeypatch.setattr(
        http_transport,
        "_urllib_response",
        lambda *args, **kwargs: response
    )

    assert http_transport._urllib_download(
        "https://example.invalid/file",
        destination
    ) == destination
    assert open(destination, "rb").read() == b"abcdef"
    assert response.closed is True


def test_download_file_uses_same_legacy_policy(monkeypatch, tmp_path):
    calls = []
    destination = str(tmp_path / "download.bin")
    _reset_preference(monkeypatch)
    monkeypatch.setattr(http_transport, "is_windows", lambda: True)
    monkeypatch.setattr(
        http_transport,
        "legacy_windows_python",
        lambda: True
    )
    monkeypatch.setattr(
        http_transport,
        "powershell_download",
        lambda *args, **kwargs: calls.append("powershell") or destination
    )
    monkeypatch.setattr(
        http_transport,
        "_urllib_download",
        lambda *args, **kwargs: calls.append("urllib") or destination
    )

    assert http_transport.download_file(
        "https://example.invalid/file",
        destination
    ) == destination
    assert calls == ["powershell"]


def test_powershell_authorization_stays_out_of_command_line(
    monkeypatch,
    tmp_path
):
    destination = str(tmp_path / "download.bin")
    with open(destination, "wb") as handle:
        handle.write(b"ok")
    captured = {}

    class FakeProcess(object):
        returncode = 0

        def communicate(self):
            return b"", b""

    def fake_popen(args, **kwargs):
        captured["args"] = args
        captured["env"] = kwargs.get("env", {})
        return FakeProcess()

    monkeypatch.setattr(
        http_transport,
        "powershell_executable",
        lambda: "powershell.exe"
    )
    monkeypatch.setattr(
        http_transport,
        "hidden_process_kwargs",
        lambda: {}
    )
    monkeypatch.setattr(
        http_transport.subprocess,
        "Popen",
        fake_popen
    )

    secret = "token do-not-expose"
    result = http_transport.powershell_download(
        "https://example.invalid/file",
        destination,
        headers={
            "Authorization": secret,
            "User-Agent": "Script-Toolbox-Test",
        },
        timeout=5
    )

    assert result == destination
    command_line = " ".join(captured["args"])
    assert secret not in command_line
    assert captured["env"][
        "SCRIPT_TOOLBOX_HTTP_AUTHORIZATION"
    ] == secret
    assert "$ErrorActionPreference = 'Stop'" in captured["args"][-1]
    assert "$responseStream.Read(" in captured["args"][-1]


def test_powershell_post_uses_request_stream_without_reserved_input(
    monkeypatch
):
    captured = {}

    class FakeProcess(object):
        returncode = 1

        def communicate(self):
            return b"", b"network failure"

    def fake_popen(args, **kwargs):
        captured["command"] = args[-1]
        return FakeProcess()

    monkeypatch.setattr(
        http_transport,
        "powershell_executable",
        lambda: "powershell.exe"
    )
    monkeypatch.setattr(
        http_transport,
        "hidden_process_kwargs",
        lambda: {}
    )
    monkeypatch.setattr(
        http_transport.subprocess,
        "Popen",
        fake_popen
    )

    with pytest.raises(http_transport.TransportError):
        http_transport.powershell_request(
            "https://example.invalid/post",
            data=b"payload",
            headers={"Content-Type": "text/plain"},
            timeout=1
        )

    command = captured["command"]
    assert "$requestStream" in command
    assert "$responseStream" in command
    assert "$input =" not in command


def test_hidden_process_kwargs_use_create_no_window(monkeypatch):
    monkeypatch.setattr(http_transport, "is_windows", lambda: True)
    kwargs = http_transport.hidden_process_kwargs()
    assert kwargs["creationflags"] == 0x08000000


def test_hidden_process_kwargs_are_empty_off_windows(monkeypatch):
    monkeypatch.setattr(http_transport, "is_windows", lambda: False)
    assert http_transport.hidden_process_kwargs() == {}
