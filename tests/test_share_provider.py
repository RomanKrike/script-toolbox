# -*- coding: utf-8 -*-

import pytest

try:
    from urllib.parse import parse_qs
except ImportError:
    from urlparse import parse_qs

from script_toolbox.core import http_transport
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


def test_share_request_uses_shared_transport(monkeypatch):
    captured = {}

    def fake_request(
        url,
        data=None,
        headers=None,
        timeout=15,
        **kwargs
    ):
        captured["url"] = url
        captured["data"] = data
        captured["headers"] = headers
        captured["timeout"] = timeout
        return b"ok"

    monkeypatch.setattr(
        http_transport,
        "request_bytes",
        fake_request
    )

    result = provider_module._request(
        "https://example.invalid/post",
        data=b"payload",
        timeout=4,
        content_type="text/plain"
    )

    assert result == b"ok"
    assert captured["data"] == b"payload"
    assert captured["headers"]["Accept"] == "text/plain"
    assert captured["headers"]["Content-Type"] == "text/plain"
    assert "Script-Toolbox-Share" in captured["headers"]["User-Agent"]
    assert captured["timeout"] == 4


def test_share_transport_failure_becomes_provider_error(monkeypatch):
    monkeypatch.setattr(
        http_transport,
        "request_bytes",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            http_transport.TransportError("offline")
        )
    )

    with pytest.raises(ShareProviderError) as error:
        provider_module._request(
            "https://example.invalid/value"
        )
    assert "offline" in str(error.value)


def test_legacy_powershell_wrapper_delegates_to_shared_transport(monkeypatch):
    captured = {}

    def fake_request(
        url,
        data=None,
        headers=None,
        timeout=15,
        method=None
    ):
        captured["url"] = url
        captured["data"] = data
        captured["headers"] = headers
        return b"legacy"

    monkeypatch.setattr(
        http_transport,
        "powershell_request",
        fake_request
    )

    assert provider_module._powershell_request(
        "https://example.invalid/post",
        data=b"payload",
        content_type="text/plain"
    ) == b"legacy"
    assert captured["headers"]["Content-Type"] == "text/plain"


def test_invalid_ids_are_rejected_before_network():
    with pytest.raises(ShareProviderError):
        PastesDevProvider().download("bad/id")
    with pytest.raises(ShareProviderError):
        DpasteProvider().download("bad/id")
