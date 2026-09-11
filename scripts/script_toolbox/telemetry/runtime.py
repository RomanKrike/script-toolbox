# -*- coding: utf-8 -*-
from __future__ import print_function

import platform
import threading
import uuid

from ..constants import BUILD_CHANNEL
from ..constants import BUILD_NUMBER
from ..constants import PLUGIN_VERSION
from ..core.preferences import get_telemetry_consent
from ..core.preferences import get_telemetry_installation_id
from ..core.preferences import set_telemetry_consent
from ..core.preferences import set_telemetry_installation_id
from ..hosts import HOST
from ..pycompat import text_type
from . import service
from .build_config import POSTHOG_HOST
from .build_config import POSTHOG_PROJECT_TOKEN
from .events import track_product_event
from .posthog_provider import PostHogProvider


_START_LOCK = threading.Lock()
_START_EVENT_SENT = False
_INSTALLATION_ID_PREFIX = "stb-install-"


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


def _get_or_create_installation_id():
    """Return ``(id, created)`` for the persisted random installation id."""
    try:
        installation_id = get_telemetry_installation_id()
    except Exception:
        installation_id = None

    if installation_id:
        return installation_id, False

    candidate = _INSTALLATION_ID_PREFIX + uuid.uuid4().hex
    try:
        installation_id = set_telemetry_installation_id(candidate)
    except Exception:
        # If persistence is unavailable, do not silently degrade to a
        # process-scoped identity because that would corrupt unique-user
        # metrics. Telemetry remains disabled instead.
        return None, False

    if not installation_id:
        return None, False

    return installation_id, True


def _ensure_posthog_provider(distinct_id=None):
    token = text_type(
        POSTHOG_PROJECT_TOKEN or ""
    ).strip()
    host = text_type(
        POSTHOG_HOST or ""
    ).strip().rstrip("/")
    distinct_id = text_type(
        distinct_id or ""
    ).strip() or None

    if not token or not host:
        return None

    try:
        provider = service.get_provider("posthog")
    except Exception:
        provider = None

    identity_matches = (
        distinct_id is None or
        (
            isinstance(provider, PostHogProvider) and
            provider.distinct_id == distinct_id
        )
    )

    if (
        isinstance(provider, PostHogProvider) and
        provider.project_token == token and
        provider.host == host and
        identity_matches
    ):
        return provider

    if provider is not None:
        try:
            provider.close()
        except Exception:
            pass

    provider = PostHogProvider(
        project_token=token,
        host=host,
        distinct_id=distinct_id
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
    True. A stable random installation id is created only when both an actual
    transport and explicit opt-in are present.
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

    if consent is not True:
        return service.configure(
            provider_name="posthog",
            enabled=False,
            common_properties=common_properties
        )

    installation_id, installation_created = _get_or_create_installation_id()
    if not installation_id:
        return service.configure(
            provider_name="posthog",
            enabled=False,
            common_properties=common_properties
        )

    try:
        provider = _ensure_posthog_provider(
            distinct_id=installation_id
        )
    except Exception:
        provider = None

    if provider is None:
        return service.configure(
            provider_name="none",
            enabled=False,
            common_properties=common_properties
        )

    status = service.configure(
        provider_name="posthog",
        enabled=True,
        common_properties=common_properties
    )

    if installation_created:
        try:
            track_product_event("installation_created")
        except Exception:
            pass

    return status


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
