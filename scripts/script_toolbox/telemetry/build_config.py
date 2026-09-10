# -*- coding: utf-8 -*-
"""Build-time telemetry configuration.

The project token is intentionally blank in source control. Official packages
stamp the public, write-only PostHog project token during GitHub Actions builds.
"""

POSTHOG_HOST = "https://eu.i.posthog.com"
POSTHOG_PROJECT_TOKEN = ""


__all__ = [
    "POSTHOG_HOST",
    "POSTHOG_PROJECT_TOKEN",
]
