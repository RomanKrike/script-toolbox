# -*- coding: utf-8 -*-
from __future__ import print_function


class TelemetryProviderError(RuntimeError):
    """Provider-specific transport or delivery failure."""


class TelemetryProvider(object):
    """Minimal provider contract used by Script Toolbox telemetry."""

    name = ""

    def capture(self, event_name, properties=None):
        """Send one event and return truthy when it was accepted."""
        raise NotImplementedError

    def flush(self):
        """Flush buffered events when a provider uses batching."""
        return True

    def close(self):
        """Release provider resources."""
        return True


class NullTelemetryProvider(TelemetryProvider):
    """No-op provider used whenever telemetry is disabled or unconfigured."""

    name = "none"

    def capture(self, event_name, properties=None):
        return False


__all__ = [
    "NullTelemetryProvider",
    "TelemetryProvider",
    "TelemetryProviderError",
]
