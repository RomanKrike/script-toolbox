# -*- coding: utf-8 -*-
from __future__ import print_function

import base64
import os

try:
    from urllib import getproxies
    from urllib import proxy_bypass
    from urllib import quote as url_quote
    from urlparse import urlsplit
except ImportError:
    from urllib.parse import quote as url_quote
    from urllib.parse import urlsplit
    from urllib.request import getproxies
    from urllib.request import proxy_bypass

from ..pycompat import text_type
from .logging_utils import get_logger


PROXY_MODE_NONE = "none"
PROXY_MODE_SYSTEM = "system"
PROXY_MODE_MANUAL = "manual"
PROXY_MODES = (
    PROXY_MODE_NONE,
    PROXY_MODE_SYSTEM,
    PROXY_MODE_MANUAL,
)

PROXY_TYPE_HTTP = "http"
PROXY_TYPE_HTTPS = "https"
PROXY_TYPE_SOCKS5 = "socks5"
PROXY_TYPES = (
    PROXY_TYPE_HTTP,
    PROXY_TYPE_HTTPS,
    PROXY_TYPE_SOCKS5,
)

_PREFERENCES_NETWORK_KEY = "network"
_PREFERENCES_PROXY_KEY = "proxy"
_PASSWORD_TOKEN_KEY = "password_protected"
_DPAPI_PREFIX = "dpapi:"
_DPAPI_DESCRIPTION = u"Script Toolbox proxy credential"


class ProxyConfigError(ValueError):
    pass


def _as_text(value):
    if value is None:
        return u""
    if isinstance(value, text_type):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return text_type(value)


def _as_bytes(value):
    if isinstance(value, bytes):
        return value
    return _as_text(value).encode("utf-8")


def normalize_proxy_mode(value, default=PROXY_MODE_SYSTEM):
    value = _as_text(value).strip().lower()
    if value in PROXY_MODES:
        return value
    return default


def normalize_proxy_type(value, default=PROXY_TYPE_HTTP):
    value = _as_text(value).strip().lower()
    if value in PROXY_TYPES:
        return value
    return default


def _normalize_host(value):
    value = _as_text(value).strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1].strip()
    return value


def _host_for_uri(host):
    host = _normalize_host(host)
    if ":" in host and not host.startswith("["):
        return "[{0}]".format(host)
    return host


class ProxyConfig(object):
    """Normalized proxy settings shared by all network transports."""

    def __init__(
        self,
        mode=PROXY_MODE_SYSTEM,
        proxy_type=PROXY_TYPE_HTTP,
        host="",
        port=None,
        requires_auth=False,
        username="",
        password=""
    ):
        self.mode = normalize_proxy_mode(mode)
        self.proxy_type = normalize_proxy_type(proxy_type)
        self.host = _normalize_host(host)
        self.port = self._normalize_port(port)
        self.requires_auth = bool(requires_auth)
        self.username = _as_text(username)
        self.password = _as_text(password)

    @staticmethod
    def _normalize_port(value):
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return value

    @classmethod
    def from_dict(cls, value, password=""):
        value = value if isinstance(value, dict) else {}
        return cls(
            mode=value.get("mode", PROXY_MODE_SYSTEM),
            proxy_type=value.get("type", PROXY_TYPE_HTTP),
            host=value.get("host", ""),
            port=value.get("port"),
            requires_auth=value.get("requires_auth", False),
            username=value.get("username", ""),
            password=password
        )

    def copy(self, **overrides):
        values = {
            "mode": self.mode,
            "proxy_type": self.proxy_type,
            "host": self.host,
            "port": self.port,
            "requires_auth": self.requires_auth,
            "username": self.username,
            "password": self.password,
        }
        values.update(overrides)
        return ProxyConfig(**values)

    def validate(self):
        if self.mode != PROXY_MODE_MANUAL:
            return self

        if not self.host:
            raise ProxyConfigError("Proxy host is required.")

        if isinstance(self.port, bool) or not isinstance(self.port, int):
            raise ProxyConfigError(
                "Proxy port must be an integer from 1 to 65535."
            )

        if self.port < 1 or self.port > 65535:
            raise ProxyConfigError(
                "Proxy port must be between 1 and 65535."
            )

        return self

    @property
    def is_manual(self):
        return self.mode == PROXY_MODE_MANUAL

    @property
    def is_socks5(self):
        return self.is_manual and self.proxy_type == PROXY_TYPE_SOCKS5

    def to_dict(self):
        return {
            "mode": self.mode,
            "type": self.proxy_type,
            "host": self.host,
            "port": self.port,
            "requires_auth": bool(self.requires_auth),
            "username": self.username if self.requires_auth else "",
        }

    def proxy_uri(self, include_credentials=True, redacted=False):
        self.validate()
        if self.mode != PROXY_MODE_MANUAL:
            return None

        scheme = (
            "socks5h"
            if self.proxy_type == PROXY_TYPE_SOCKS5
            else self.proxy_type
        )
        credentials = ""
        if include_credentials and self.requires_auth:
            username = url_quote(_as_bytes(self.username), safe="")
            if not isinstance(username, text_type):
                username = _as_text(username)
            if redacted:
                password = "***"
            else:
                password = url_quote(_as_bytes(self.password), safe="")
                if not isinstance(password, text_type):
                    password = _as_text(password)
            credentials = "{0}:{1}@".format(username, password)

        return "{0}://{1}{2}:{3}".format(
            scheme,
            credentials,
            _host_for_uri(self.host),
            self.port
        )

    def redacted_uri(self):
        return self.proxy_uri(
            include_credentials=True,
            redacted=True
        )

    def debug_summary(self):
        if self.mode != PROXY_MODE_MANUAL:
            return "Proxy mode: {0}".format(self.mode)
        return (
            "Proxy mode: manual; type: {0}; host: {1}; "
            "port: {2}; authentication: {3}"
        ).format(
            self.proxy_type.upper(),
            self.host,
            self.port,
            "enabled" if self.requires_auth else "disabled"
        )


def _network_dict(preferences):
    value = preferences.get(_PREFERENCES_NETWORK_KEY, {})
    return value if isinstance(value, dict) else {}


def _proxy_dict(preferences):
    value = _network_dict(preferences).get(_PREFERENCES_PROXY_KEY, {})
    return value if isinstance(value, dict) else {}


def _dpapi_available():
    return os.name == "nt"


def _dpapi_crypt(data, protect):
    """Protect/unprotect bytes with Windows DPAPI without dependencies."""
    if not _dpapi_available():
        return None

    try:
        import ctypes
        from ctypes import wintypes
    except Exception:
        return None

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]

    raw = _as_bytes(data)
    buffer_value = ctypes.create_string_buffer(raw, len(raw))
    input_blob = DATA_BLOB(
        len(raw),
        ctypes.cast(buffer_value, ctypes.POINTER(ctypes.c_byte))
    )
    output_blob = DATA_BLOB()

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    if protect:
        success = crypt32.CryptProtectData(
            ctypes.byref(input_blob),
            ctypes.c_wchar_p(_DPAPI_DESCRIPTION),
            None,
            None,
            None,
            0,
            ctypes.byref(output_blob)
        )
    else:
        success = crypt32.CryptUnprotectData(
            ctypes.byref(input_blob),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(output_blob)
        )

    if not success:
        return None

    try:
        return ctypes.string_at(
            output_blob.pbData,
            output_blob.cbData
        )
    finally:
        try:
            kernel32.LocalFree(output_blob.pbData)
        except Exception:
            pass


def protect_password(password):
    password = _as_text(password)
    if not password:
        return ""

    protected = _dpapi_crypt(password, True)
    if protected is None:
        return None

    encoded = base64.b64encode(protected)
    return _DPAPI_PREFIX + _as_text(encoded)


def unprotect_password(token):
    token = _as_text(token).strip()
    if not token:
        return ""
    if not token.startswith(_DPAPI_PREFIX):
        return ""

    try:
        protected = base64.b64decode(
            _as_bytes(token[len(_DPAPI_PREFIX):])
        )
    except Exception:
        return ""

    clear = _dpapi_crypt(protected, False)
    if clear is None:
        return ""
    return _as_text(clear)


def secure_password_storage_available():
    return _dpapi_available()


def load_proxy_config(path=None):
    """Load settings; absent legacy config preserves system proxy behavior."""
    from .preferences import load_preferences

    preferences = load_preferences(path=path)
    stored = _proxy_dict(preferences)
    password = unprotect_password(
        stored.get(_PASSWORD_TOKEN_KEY, "")
    )
    config = ProxyConfig.from_dict(stored, password=password)
    try:
        config.validate()
    except ProxyConfigError:
        return ProxyConfig(mode=PROXY_MODE_SYSTEM)
    return config


def save_proxy_config(config, path=None):
    """Persist settings without ever writing the clear-text password."""
    from .preferences import load_preferences
    from .preferences import save_preferences

    if not isinstance(config, ProxyConfig):
        config = ProxyConfig.from_dict(config or {})
    config.validate()

    preferences = load_preferences(path=path)
    network = dict(_network_dict(preferences))
    stored = config.to_dict()
    password_persisted = True

    if config.requires_auth and config.password:
        token = protect_password(config.password)
        if token:
            stored[_PASSWORD_TOKEN_KEY] = token
        else:
            password_persisted = False
    elif config.requires_auth:
        previous = _proxy_dict(preferences).get(_PASSWORD_TOKEN_KEY, "")
        if previous:
            stored[_PASSWORD_TOKEN_KEY] = previous

    network[_PREFERENCES_PROXY_KEY] = stored
    preferences[_PREFERENCES_NETWORK_KEY] = network
    save_preferences(preferences, path=path)
    return password_persisted


def clear_proxy_password(path=None):
    from .preferences import load_preferences
    from .preferences import save_preferences

    preferences = load_preferences(path=path)
    network = dict(_network_dict(preferences))
    proxy = dict(_proxy_dict(preferences))
    proxy.pop(_PASSWORD_TOKEN_KEY, None)
    network[_PREFERENCES_PROXY_KEY] = proxy
    preferences[_PREFERENCES_NETWORK_KEY] = network
    save_preferences(preferences, path=path)


def system_proxy_for_url(url):
    """Return proxy URI, empty string for bypass, or None for OS default."""
    try:
        parts = urlsplit(_as_text(url))
        host = parts.hostname or ""
        if host and proxy_bypass(host):
            return ""

        proxies = getproxies() or {}
        scheme = (parts.scheme or "https").lower()
        proxy = (
            proxies.get(scheme) or
            proxies.get("all") or
            proxies.get("ALL")
        )
        if proxy:
            return _as_text(proxy).strip()
    except Exception:
        return None
    return None


def redact_text(value, config=None):
    value = _as_text(value)
    config = config if isinstance(config, ProxyConfig) else None
    if config is None:
        return value

    if config.requires_auth:
        try:
            full_uri = config.proxy_uri(
                include_credentials=True,
                redacted=False
            )
            redacted_uri = config.redacted_uri()
            if full_uri and redacted_uri:
                value = value.replace(full_uri, redacted_uri)
        except Exception:
            pass

    if config.password:
        value = value.replace(config.password, "***")
    return value


def log_proxy_config(config):
    logger = get_logger()
    if not isinstance(config, ProxyConfig):
        config = ProxyConfig.from_dict(config or {})
    logger.debug(config.debug_summary())


def parse_proxy_uri(uri, default_type=PROXY_TYPE_HTTP):
    """Normalize a proxy URI returned by the OS/environment."""
    uri = _as_text(uri).strip()
    if not uri:
        return None
    parts = urlsplit(uri)
    scheme = (parts.scheme or default_type).lower()
    proxy_type = scheme
    if scheme in ("socks", "socks5h"):
        proxy_type = PROXY_TYPE_SOCKS5
    if proxy_type not in PROXY_TYPES:
        proxy_type = default_type
    port = parts.port
    if port is None:
        port = 443 if proxy_type == PROXY_TYPE_HTTPS else 80
        if proxy_type == PROXY_TYPE_SOCKS5:
            port = 1080
    return ProxyConfig(
        mode=PROXY_MODE_MANUAL,
        proxy_type=proxy_type,
        host=parts.hostname or "",
        port=port,
        requires_auth=parts.username is not None,
        username=parts.username or "",
        password=parts.password or ""
    )


__all__ = [
    "PROXY_MODE_MANUAL",
    "PROXY_MODE_NONE",
    "PROXY_MODE_SYSTEM",
    "PROXY_MODES",
    "PROXY_TYPE_HTTP",
    "PROXY_TYPE_HTTPS",
    "PROXY_TYPE_SOCKS5",
    "PROXY_TYPES",
    "ProxyConfig",
    "ProxyConfigError",
    "clear_proxy_password",
    "load_proxy_config",
    "log_proxy_config",
    "normalize_proxy_mode",
    "normalize_proxy_type",
    "parse_proxy_uri",
    "protect_password",
    "redact_text",
    "save_proxy_config",
    "secure_password_storage_available",
    "system_proxy_for_url",
    "unprotect_password",
]
