# Telemetry architecture

Script Toolbox telemetry is optional, explicit opt-in, and provider-agnostic.

The core plugin must never depend on PostHog, Aptabase, or any future analytics service directly. Feature code only emits semantic events through the `script_toolbox.telemetry` facade.

## Privacy contract

Telemetry must remain disabled until the user explicitly opts in.

The persisted preference is tri-state:

- `None` — the user has not answered yet;
- `True` — the user explicitly opted in;
- `False` — the user explicitly opted out.

A provider being configured does not imply consent. The application bootstrap must enable telemetry only when `get_telemetry_consent()` is exactly `True`.

Telemetry must not collect scene contents, filenames, file paths, object names, scripts, Autodesk account information, OS usernames, hostnames, or other personal/project data.

Provider failures must never affect normal Script Toolbox behavior. Event delivery is best-effort and failures are swallowed by the telemetry facade.

## Provider boundary

Concrete backends implement the small `TelemetryProvider` contract:

```python
from script_toolbox.telemetry import TelemetryProvider


class MyAnalyticsProvider(TelemetryProvider):
    name = "my-service"

    def capture(self, event_name, properties=None):
        # Send the event to the analytics backend.
        return True
```

Register and select the provider during application bootstrap:

```python
from script_toolbox import telemetry
from script_toolbox.core.preferences import get_telemetry_consent

provider = MyAnalyticsProvider()
telemetry.register_provider(provider)
telemetry.configure(
    provider_name="my-service",
    enabled=(get_telemetry_consent() is True),
    common_properties={
        "plugin_version": "...",
        "host": "maya",
    },
)
```

Feature code remains backend-independent:

```python
from script_toolbox import telemetry

telemetry.track(
    "item_created",
    {"item_type": "field"},
)
```

Changing from PostHog to a custom Script Toolbox analytics service should therefore require replacing provider registration/bootstrap configuration, not rewriting feature code or UI event instrumentation.

## Built-in null provider

`NullTelemetryProvider` is always registered as `none` and is the default provider. Fresh installs therefore have no active telemetry transport.

The null provider is also the safe fallback for development, tests, unavailable services, and builds that do not configure an analytics backend.

## Provider selection

Provider selection is runtime/build configuration, not a user preference. This prevents an old persisted provider name from pinning users to a backend after Script Toolbox changes analytics services.

The user's persisted setting controls only consent.

## Event design

Events should describe product behavior rather than UI implementation details. Prefer stable names such as:

```text
plugin_started
editor_opened
config_imported
config_exported
item_created
item_duplicated
share_created
```

Properties should be low-cardinality technical metadata, for example:

```text
plugin_version
build_channel
host
host_version
os
item_type
```

Do not send arbitrary strings originating from user scenes, scripts, paths, labels, object names, or config content.

## Switching providers

A provider switch should follow this sequence:

1. Implement a new `TelemetryProvider`.
2. Add provider-specific tests.
3. Register it during bootstrap.
4. Select it in `telemetry.configure(...)`.
5. Keep the event schema stable unless a product requirement explicitly changes it.

This boundary is intended to support PostHog initially and a self-hosted/custom Script Toolbox analytics service later without coupling either backend to the rest of the plugin.
