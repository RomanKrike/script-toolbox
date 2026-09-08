# -*- coding: utf-8 -*-

try:
    from urllib.parse import parse_qs
except ImportError:
    from urlparse import parse_qs

from script_toolbox.share import provider as provider_module
from script_toolbox.share.provider import DpasteProvider


def test_dpaste_upload_uses_plain_text_contract(monkeypatch):
    captured = {}

    def fake_request(url, data=None, timeout=15):
        captured["url"] = url
        captured["data"] = data
        captured["timeout"] = timeout
        return b"https://dpaste.com/ABC123\n"

    monkeypatch.setattr(
        provider_module,
        "_request",
        fake_request
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


def test_dpaste_download_uses_raw_text_endpoint(monkeypatch):
    captured = {}

    def fake_request(url, data=None, timeout=15):
        captured["url"] = url
        return b"encrypted-payload\n"

    monkeypatch.setattr(
        provider_module,
        "_request",
        fake_request
    )

    provider = DpasteProvider()

    assert provider.download("ABC123") == "encrypted-payload"
    assert captured["url"] == "https://dpaste.com/ABC123.txt"
