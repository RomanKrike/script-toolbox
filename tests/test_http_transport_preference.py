# -*- coding: utf-8 -*-

import pytest

from script_toolbox.core import http_transport


def _modern_windows(monkeypatch):
    monkeypatch.setattr(
        http_transport,
        "_WINDOWS_POWERSHELL_PREFERRED",
        [False]
    )
    monkeypatch.setattr(http_transport, "is_windows", lambda: True)
    monkeypatch.setattr(
        http_transport,
        "legacy_windows_python",
        lambda: False
    )


def test_failed_request_fallback_is_not_remembered(monkeypatch):
    _modern_windows(monkeypatch)
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

    with pytest.raises(http_transport.TransportError):
        http_transport.request_bytes("https://example.invalid/value")

    assert http_transport._WINDOWS_POWERSHELL_PREFERRED[0] is False


def test_failed_download_fallback_is_not_remembered(monkeypatch, tmp_path):
    _modern_windows(monkeypatch)
    destination = str(tmp_path / "download.bin")
    monkeypatch.setattr(
        http_transport,
        "_urllib_download",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            IOError("urllib failed")
        )
    )
    monkeypatch.setattr(
        http_transport,
        "powershell_download",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            http_transport.TransportError("powershell failed")
        )
    )

    with pytest.raises(http_transport.TransportError):
        http_transport.download_file(
            "https://example.invalid/file",
            destination
        )

    assert http_transport._WINDOWS_POWERSHELL_PREFERRED[0] is False
