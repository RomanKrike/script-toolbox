# -*- coding: utf-8 -*-
from __future__ import print_function

import threading

from ..pycompat import text_type
from .provider import NullTelemetryProvider


class TelemetryError(RuntimeError):
    pass


_LOCK = threading.RLock()
_PROVIDERS = {
    "none": NullTelemetryProvider(),
}
_ACTIVE_PROVIDER = "none"
_ENABLED = False
_COMMON_PROPERTIES = {}


def _normalize_provider_name(value):
    return text_type(value or "").strip().lower()


def _copy_properties(properties):
    if properties is None:
        return {}
    if not isinstance(properties, dict):
        raise TelemetryError(
            "Telemetry properties must be a dictionary."
        )
    return dict(properties)


def register_provider(provider, replace=False):
    """Register a provider implementation by its stable ``name``."""
    name = _normalize_provider_name(
        getattr(provider, "name", "")
    )

    if not name:
        raise TelemetryError(
            "Telemetry provider must define a name."
        )
    if not callable(getattr(provider, "capture", None)):
        raise TelemetryError(
            "Telemetry provider must define capture()."
        )

    with _LOCK:
        if name in _PROVIDERS and not replace:
            raise TelemetryError(
                "Telemetry provider already registered: {0}".format(name)
            )
        _PROVIDERS[name] = provider

    return provider


def unregister_provider(name):
    """Remove a non-null provider from the registry."""
    global _ACTIVE_PROVIDER

    name = _normalize_provider_name(name)
    if name == "none":
        return False

    with _LOCK:
        removed = _PROVIDERS.pop(name, None)
        if _ACTIVE_PROVIDER == name:
            _ACTIVE_PROVIDER = "none"

    return removed is not None


def get_provider(name):
    name = _normalize_provider_name(name)
    with _LOCK:
        provider = _PROVIDERS.get(name)

    if provider is None:
        raise TelemetryError(
            "Unknown telemetry provider: {0}".format(name)
        )
    return provider


def available_provider_names():
    with _LOCK:
        return tuple(sorted(_PROVIDERS.keys()))


def configure(
    provider_name="none",
    enabled=False,
    common_properties=None
):
    """Configure the process-wide telemetry facade.

    Provider selection is intentionally runtime configuration rather than
    business-logic state. Callers only use ``track()`` and never import a
    concrete analytics backend.
    """
    global _ACTIVE_PROVIDER
    global _COMMON_PROPERTIES
    global _ENABLED

    provider_name = _normalize_provider_name(provider_name) or "none"
    properties = _copy_properties(common_properties)

    # Validate before mutating global state.
    get_provider(provider_name)

    with _LOCK:
        _ACTIVE_PROVIDER = provider_name
        _ENABLED = bool(enabled)
        _COMMON_PROPERTIES = properties

    return status()


def set_provider(provider_name):
    global _ACTIVE_PROVIDER

    provider_name = _normalize_provider_name(provider_name) or "none"
    get_provider(provider_name)

    with _LOCK:
        _ACTIVE_PROVIDER = provider_name

    return provider_name


def set_enabled(enabled):
    global _ENABLED

    with _LOCK:
        _ENABLED = bool(enabled)
        return _ENABLED


def is_enabled():
    with _LOCK:
        return bool(_ENABLED)


def active_provider_name():
    with _LOCK:
        return _ACTIVE_PROVIDER


def set_common_properties(properties=None):
    global _COMMON_PROPERTIES

    properties = _copy_properties(properties)
    with _LOCK:
        _COMMON_PROPERTIES = properties
    return dict(properties)


def common_properties():
    with _LOCK:
        return dict(_COMMON_PROPERTIES)


def status():
    with _LOCK:
        return {
            "enabled": bool(_ENABLED),
            "provider": _ACTIVE_PROVIDER,
            "providers": tuple(sorted(_PROVIDERS.keys())),
        }


def track(event_name, properties=None):
    """Capture an event without ever breaking Script Toolbox execution.

    Delivery errors are intentionally swallowed. Telemetry is optional and
    must never affect plugin functionality.
    """
    event_name = text_type(event_name or "").strip()
    if not event_name:
        return False

    try:
        event_properties = _copy_properties(properties)
    except TelemetryError:
        return False

    with _LOCK:
        if not _ENABLED:
            return False
        provider = _PROVIDERS.get(_ACTIVE_PROVIDER)
        if provider is None:
            return False
        payload = dict(_COMMON_PROPERTIES)

    payload.update(event_properties)

    try:
        return bool(
            provider.capture(
                event_name,
                payload
            )
        )
    except Exception:
        return False


def flush():
    with _LOCK:
        if not _ENABLED:
            return False
        provider = _PROVIDERS.get(_ACTIVE_PROVIDER)

    if provider is None:
        return False

    try:
        return bool(provider.flush())
    except Exception:
        return False


def close():
    with _LOCK:
        provider = _PROVIDERS.get(_ACTIVE_PROVIDER)

    if provider is None:
        return False

    try:
        return bool(provider.close())
    except Exception:
        return False


def reset():
    """Reset runtime state while retaining only the built-in null provider."""
    global _ACTIVE_PROVIDER
    global _COMMON_PROPERTIES
    global _ENABLED

    with _LOCK:
        null_provider = _PROVIDERS.get("none") or NullTelemetryProvider()
        _PROVIDERS.clear()
        _PROVIDERS["none"] = null_provider
        _ACTIVE_PROVIDER = "none"
        _ENABLED = False
        _COMMON_PROPERTIES = {}


__all__ = [
    "TelemetryError",
    "active_provider_name",
    "available_provider_names",
    "close",
    "common_properties",
    "configure",
    "flush",
    "get_provider",
    "is_enabled",
    "register_provider",
    "reset",
    "set_common_properties",
    "set_enabled",
    "set_provider",
    "status",
    "track",
    "unregister_provider",
]
