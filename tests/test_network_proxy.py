# -*- coding: utf-8 -*-

import json

import pytest

from script_toolbox.core import http_transport
from script_toolbox.core import network_proxy


def _manual(proxy_type="http", **kwargs):
    values = {
        "mode": network_proxy.PROXY_MODE_MANUAL,
        "proxy_type": proxy_type,
        "host": "proxy.company.local",
        "port": 8080,
        "requires_auth": False,
        "username": "",
        "password": "",
    }
    values.update(kwargs)
    return network_proxy.ProxyConfig(**values)


def test_missing_proxy_preferences_preserve_system_behavior(tmp_path):
    config = network_proxy.load_proxy_config(
        path=str(tmp_path / "settings.json")
    )
    assert config.mode == network_proxy.PROXY_MODE_SYSTEM


@pytest.mark.parametrize("proxy_type", ["http", "https", "socks5"])
def test_manual_proxy_types_create_normalized_uri(proxy_type):
    config = _manual(proxy_type)
    uri = config.proxy_uri()
    expected_scheme = "socks5h" if proxy_type == "socks5" else proxy_type
    assert uri == (
        "{0}://proxy.company.local:8080".format(expected_scheme)
    )


def test_proxy_credentials_are_url_encoded():
    config = _manual(
        requires_auth=True,
        username="user@company",
        password="p:a/s#%"
    )
    assert config.proxy_uri() == (
        "http://user%40company:p%3Aa%2Fs%23%25@"
        "proxy.company.local:8080"
    )
    assert config.redacted_uri() == (
        "http://user%40company:***@proxy.company.local:8080"
    )


def test_ipv6_host_is_bracketed_in_proxy_uri():
    config = _manual(
        proxy_type="socks5",
        host="2001:db8::1",
        port=1080
    )
    assert config.proxy_uri() == "socks5h://[2001:db8::1]:1080"


@pytest.mark.parametrize("port", [0, 65536, "invalid"])
def test_invalid_manual_port_is_rejected(port):
    with pytest.raises(network_proxy.ProxyConfigError):
        _manual(port=port).validate()


def test_empty_manual_host_is_rejected():
    with pytest.raises(network_proxy.ProxyConfigError):
        _manual(host="").validate()


def test_no_proxy_and_system_proxy_do_not_require_manual_fields():
    network_proxy.ProxyConfig(
        mode=network_proxy.PROXY_MODE_NONE
    ).validate()
    network_proxy.ProxyConfig(
        mode=network_proxy.PROXY_MODE_SYSTEM
    ).validate()


def test_proxy_config_round_trip_without_password(tmp_path):
    path = str(tmp_path / "settings.json")
    source = _manual(
        proxy_type="https",
        host=" proxy.internal ",
        port=8443,
        requires_auth=False
    )

    assert network_proxy.save_proxy_config(source, path=path) is True
    loaded = network_proxy.load_proxy_config(path=path)

    assert loaded.mode == network_proxy.PROXY_MODE_MANUAL
    assert loaded.proxy_type == network_proxy.PROXY_TYPE_HTTPS
    assert loaded.host == "proxy.internal"
    assert loaded.port == 8443
    assert loaded.password == ""


def test_password_is_never_written_in_clear_text(tmp_path, monkeypatch):
    path = str(tmp_path / "settings.json")
    monkeypatch.setattr(
        network_proxy,
        "protect_password",
        lambda password: "dpapi:encrypted-value"
    )
    monkeypatch.setattr(
        network_proxy,
        "unprotect_password",
        lambda token: "secret-value" if token else ""
    )

    source = _manual(
        requires_auth=True,
        username="roman",
        password="secret-value"
    )
    assert network_proxy.save_proxy_config(source, path=path) is True

    text = open(path, "r").read()
    data = json.loads(text)
    assert "secret-value" not in text
    assert data["network"]["proxy"]["password_protected"] == (
        "dpapi:encrypted-value"
    )
    assert network_proxy.load_proxy_config(path=path).password == (
        "secret-value"
    )


def test_password_is_not_downgraded_to_plain_text_without_secure_backend(
    tmp_path,
    monkeypatch
):
    path = str(tmp_path / "settings.json")
    monkeypatch.setattr(
        network_proxy,
        "protect_password",
        lambda password: None
    )

    source = _manual(
        requires_auth=True,
        username="roman",
        password="secret-value"
    )
    assert network_proxy.save_proxy_config(source, path=path) is False
    assert "secret-value" not in open(path, "r").read()


def test_redact_text_removes_password_and_full_credential_uri():
    config = _manual(
        requires_auth=True,
        username="roman",
        password="very-secret"
    )
    message = (
        "failed via {0}; password=very-secret".format(
            config.proxy_uri()
        )
    )
    redacted = network_proxy.redact_text(message, config)
    assert "very-secret" not in redacted
    assert "***" in redacted


def test_manual_http_proxy_builds_one_opener_for_http_and_https():
    config = _manual("http")
    opener = http_transport._urllib_opener(config)
    handlers = [
        handler for handler in opener.handlers
        if isinstance(handler, http_transport.ProxyHandler)
    ]
    assert len(handlers) == 1
    assert handlers[0].proxies["http"].startswith("http://")
    assert handlers[0].proxies["https"].startswith("http://")


def test_manual_https_proxy_builds_https_proxy_uri():
    config = _manual("https", port=8443)
    opener = http_transport._urllib_opener(config)
    handlers = [
        handler for handler in opener.handlers
        if isinstance(handler, http_transport.ProxyHandler)
    ]
    assert handlers[0].proxies["http"].startswith("https://")
    assert handlers[0].proxies["https"].startswith("https://")


def test_socks5_uses_dedicated_handlers_and_disables_powershell(monkeypatch):
    config = _manual("socks5", port=1080)
    opener = http_transport._urllib_opener(config)
    names = [type(handler).__name__ for handler in opener.handlers]
    assert "_SocksHTTPHandler" in names
    assert "_SocksHTTPSHandler" in names

    monkeypatch.setattr(http_transport, "is_windows", lambda: True)
    monkeypatch.setattr(
        http_transport,
        "legacy_windows_python",
        lambda: True
    )
    assert http_transport._prefer_powershell(
        None,
        proxy_config=config
    ) is False


def test_no_proxy_builds_an_explicit_direct_opener():
    config = network_proxy.ProxyConfig(
        mode=network_proxy.PROXY_MODE_NONE
    )
    opener = http_transport._urllib_opener(config)
    assert opener is not None
    handlers = [
        handler for handler in opener.handlers
        if isinstance(handler, http_transport.ProxyHandler)
    ]
    assert handlers == []


def test_system_proxy_keeps_standard_urlopen_path():
    config = network_proxy.ProxyConfig(
        mode=network_proxy.PROXY_MODE_SYSTEM
    )
    assert http_transport._urllib_opener(config) is None


def test_powershell_proxy_credentials_stay_out_of_command_line(
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
        captured["env"] = kwargs["env"]
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

    config = _manual(
        requires_auth=True,
        username="roman",
        password="secret-value"
    )
    http_transport.powershell_download(
        "https://example.invalid/file",
        destination,
        proxy_config=config
    )

    command_line = " ".join(captured["args"])
    assert "secret-value" not in command_line
    assert captured["env"]["SCRIPT_TOOLBOX_PROXY_USERNAME"] == "roman"
    assert captured["env"]["SCRIPT_TOOLBOX_PROXY_PASSWORD"] == "secret-value"


def test_proxy_auth_error_has_actionable_message():
    config = _manual(
        requires_auth=True,
        username="roman",
        password="secret"
    )
    error = http_transport.TransportError(
        "407 Proxy Authentication Required",
        kind="proxy_auth"
    )
    message = http_transport.user_error_message(
        error,
        proxy_config=config
    )
    assert "Proxy authentication required" in message
    assert "secret" not in message


def test_redirects_reuse_same_opener_proxy_configuration():
    config = _manual("http")
    opener = http_transport._urllib_opener(config)
    handler_names = [type(handler).__name__ for handler in opener.handlers]
    assert "HTTPRedirectHandler" in handler_names
    proxy_handlers = [
        handler for handler in opener.handlers
        if isinstance(handler, http_transport.ProxyHandler)
    ]
    assert len(proxy_handlers) == 1
