# -*- coding: utf-8 -*-
from __future__ import print_function

import platform
import threading

from ..constants import BUILD_CHANNEL
from ..constants import BUILD_NUMBER
from ..constants import PLUGIN_VERSION
from ..core.preferences import get_telemetry_consent
from ..core.preferences import set_telemetry_consent
from ..hosts import HOST
from ..pycompat import text_type
from . import service
from .build_config import POSTHOG_HOST
from .build_config import POSTHOG_PROJECT_TOKEN
from .events import track_product_event
from .posthog_provider import PostHogProvider


_START_LOCK = threading.Lock()
_START_EVENT_SENT = False


def _host_version():
    try:
        return text_type(
            HOST.app_version() or ""
        ).strip()
    except Exception:
        return ""


def _os_name():
    try:
        return text_type(
            platform.system() or "unknown"
        ).strip().lower()
    except Exception:
        return "unknown"


def default_common_properties():
    """Return the privacy-reviewed technical metadata sent on every event."""
    return {
        "plugin_version": PLUGIN_VERSION,
        "build_channel": BUILD_CHANNEL,
        "build_number": int(BUILD_NUMBER or 0),
        "host": text_type(
            getattr(HOST, "key", "standalone") or "standalone"
        ),
        "host_version": _host_version(),
        "os": _os_name(),
    }


def _ensure_posthog_provider():
    token = text_type(
        POSTHOG_PROJECT_TOKEN or ""
    ).strip()
    host = text_type(
        POSTHOG_HOST or ""
    ).strip().rstrip("/")

    if not token or not host:
        return None

    try:
        provider = service.get_provider("posthog")
    except Exception:
        provider = None

    if (
        isinstance(provider, PostHogProvider) and
        provider.project_token == token and
        provider.host == host
    ):
        return provider

    if provider is not None:
        try:
            provider.close()
        except Exception:
            pass

    provider = PostHogProvider(
        project_token=token,
        host=host
    )
    service.register_provider(
        provider,
        replace=True
    )
    return provider


def configure_default_telemetry():
    """Configure the official build provider from consent + build config.

    A stamped PostHog token only makes the transport available. Network event
    delivery remains disabled unless the persisted consent value is exactly
    True.
    """
    consent = get_telemetry_consent()
    common_properties = default_common_properties()

    try:
        provider = _ensure_posthog_provider()
    except Exception:
        provider = None

    if provider is None:
        return service.configure(
            provider_name="none",
            enabled=False,
            common_properties=common_properties
        )

    return service.configure(
        provider_name="posthog",
        enabled=(consent is True),
        common_properties=common_properties
    )


def initialize_telemetry():
    """Configure telemetry and emit one startup event per loaded runtime."""
    global _START_EVENT_SENT

    status = configure_default_telemetry()

    if not status.get("enabled"):
        return status

    with _START_LOCK:
        if _START_EVENT_SENT:
            return status

        if track_product_event("plugin_started"):
            _START_EVENT_SENT = True

    return status


def refresh_telemetry():
    """Re-read consent/build configuration after a settings change."""
    return configure_default_telemetry()


def apply_telemetry_consent(consent):
    """Persist a consent choice and immediately apply it to this runtime."""
    consent = set_telemetry_consent(consent)

    if consent is True:
        return initialize_telemetry()

    return refresh_telemetry()


__all__ = [
    "apply_telemetry_consent",
    "configure_default_telemetry",
    "default_common_properties",
    "initialize_telemetry",
    "refresh_telemetry",
]
