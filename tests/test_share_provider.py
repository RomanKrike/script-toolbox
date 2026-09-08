# -*- coding: utf-8 -*-

import pytest

try:
    from urllib.parse import parse_qs
except ImportError:
    from urlparse import parse_qs

from script_toolbox.share import provider as provider_module
from script_toolbox.share.provider import DpasteProvider
from script_toolbox.share.provider import PastesDevProvider
from script_toolbox.share.provider import ShareProviderError


def test_pastes_dev_upload_uses_raw_text_contract(monkeypatch):
    captured = {}

    def fake_request(
        url,
        data=None,
        timeout=15,
        content_type=None
    ):
        captured["url"] = url
        captured["data"] = data
        captured["timeout"] = timeout
        captured["content_type"] = content_type
        return b'{"key":"ABC123"}'

    monkeypatch.setattr(
        provider_module,
        "_request",
        fake_request
    )

    provider = PastesDevProvider()
    paste_id = provider.upload(
        "encrypted-payload",
        expiry_days=14
    )

    assert paste_id == "ABC123"
    assert captured["url"] == provider.api_url
    assert captured["data"] == b"encrypted-payload"
    assert captured["content_type"] == "text/plain; charset=utf-8"


def test_pastes_dev_download_uses_api_key_endpoint(monkeypatch):
    captured = {}

    def fake_request(
        url,
        data=None,
        timeout=15,
        content_type=None
    ):
        captured["url"] = url
        return b"encrypted-payload\n"

    monkeypatch.setattr(
        provider_module,
        "_request",
        fake_request
    )

    provider = PastesDevProvider()

    assert provider.download("ABC123") == "encrypted-payload"
    assert captured["url"] == "https://api.pastes.dev/ABC123"


def test_dpaste_upload_uses_plain_text_contract(monkeypatch):
    captured = {}

    def fake_request(
        url,
        data=None,
        timeout=15,
        content_type=None
    ):
        captured["url"] = url
        captured["data"] = data
        captured["timeout"] = timeout
        captured["content_type"] = content_type
        return b"https://dpaste.com/ABC123\n"

    monkeypatch.setattr(
        provider_module,
        "_request",
        fake_request
    )
    monkeypatch.setattr(
        provider_module,
        "_throttle",
        lambda: None
    )

    provider = DpasteProvider()
    paste_id = provider.upload(
        "encrypted-payload",
        expiry_days=14
    )
    form = parse_qs(captured["data"])

    assert paste_id == "ABC123"
    assert captured["url"] == provider.api_url
    assert form["content"] == ["encrypted-payload"]
    assert form["expiry_days"] == ["14"]
    assert form["title"] == ["Script Toolbox encrypted share"]
    assert "syntax" not in form
    assert captured["content_type"] == "application/x-www-form-urlencoded"


def test_dpaste_download_uses_raw_text_endpoint(monkeypatch):
    captured = {}

    def fake_request(
        url,
        data=None,
        timeout=15,
        content_type=None
    ):
        captured["url"] = url
        return b"encrypted-payload\n"

    monkeypatch.setattr(
        provider_module,
        "_request",
        fake_request
    )
    monkeypatch.setattr(
        provider_module,
        "_throttle",
        lambda: None
    )

    provider = DpasteProvider()

    assert provider.download("ABC123") == "encrypted-payload"
    assert captured["url"] == "https://dpaste.com/ABC123.txt"


def test_powershell_transport_avoids_reserved_input_variable(monkeypatch):
    captured = {}

    class FakeProcess(object):
        returncode = 1

        def communicate(self):
            return b"", b"network failure"

    def fake_popen(arguments, **kwargs):
        captured["command"] = arguments[-1]
        return FakeProcess()

    monkeypatch.setattr(
        provider_module,
        "_powershell_executable",
        lambda: "powershell.exe"
    )
    monkeypatch.setattr(
        provider_module.subprocess,
        "Popen",
        fake_popen
    )

    with pytest.raises(ShareProviderError):
        provider_module._powershell_request(
            "https://example.invalid/post",
            data=b"payload",
            timeout=1,
            content_type="text/plain"
        )

    command = captured["command"]
    assert "$ErrorActionPreference = 'Stop'" in command
    assert "$requestStream" in command
    assert "$responseStream" in command
    assert "$input =" not in command


def test_legacy_windows_request_uses_powershell_before_urllib(monkeypatch):
    calls = []

    monkeypatch.setattr(
        provider_module,
        "_is_windows",
        lambda: True
    )
    monkeypatch.setattr(
        provider_module,
        "_legacy_windows_python",
        lambda: True
    )
    monkeypatch.setattr(
        provider_module,
        "_WINDOWS_POWERSHELL_PREFERRED",
        [False]
    )

    def fake_powershell(
        url,
        data=None,
        timeout=15,
        content_type=None
    ):
        calls.append("powershell")
        return b"fast-response"

    def fail_urlopen(*args, **kwargs):
        calls.append("urllib")
        raise AssertionError(
            "urllib should not run before PowerShell on legacy Windows Python"
        )

    monkeypatch.setattr(
        provider_module,
        "_powershell_request",
        fake_powershell
    )
    monkeypatch.setattr(
        provider_module,
        "urlopen",
        fail_urlopen
    )

    result = provider_module._request(
        "https://example.invalid/value"
    )

    assert result == b"fast-response"
    assert calls == ["powershell"]


def test_windows_remembers_successful_powershell_fallback(monkeypatch):
    calls = []

    monkeypatch.setattr(
        provider_module,
        "_is_windows",
        lambda: True
    )
    monkeypatch.setattr(
        provider_module,
        "_legacy_windows_python",
        lambda: False
    )
    monkeypatch.setattr(
        provider_module,
        "_WINDOWS_POWERSHELL_PREFERRED",
        [False]
    )

    def fake_urlopen(request, timeout=15):
        calls.append("urllib")
        raise IOError("TLS failure")

    def fake_powershell(
        url,
        data=None,
        timeout=15,
        content_type=None
    ):
        calls.append("powershell")
        return b"fallback-response"

    monkeypatch.setattr(
        provider_module,
        "urlopen",
        fake_urlopen
    )
    monkeypatch.setattr(
        provider_module,
        "_powershell_request",
        fake_powershell
    )

    first = provider_module._request(
        "https://example.invalid/first"
    )
    second = provider_module._request(
        "https://example.invalid/second"
    )

    assert first == b"fallback-response"
    assert second == b"fallback-response"
    assert calls == [
        "urllib",
        "powershell",
        "powershell",
    ]
