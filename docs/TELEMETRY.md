# Telemetry architecture

Script Toolbox telemetry is optional, explicit opt-in, and provider-agnostic.

The core plugin must never depend on PostHog, Aptabase, or any future analytics service directly. Feature code only emits semantic events through the `script_toolbox.telemetry` facade.

## Privacy contract

Telemetry must remain disabled until the user explicitly opts in.

The persisted preference is tri-state:

- `None` — the user has not answered yet;
- `True` — the user explicitly opted in;
- `False` — the user explicitly opted out.

A provider being configured does not imply consent. The application bootstrap enables telemetry only when `get_telemetry_consent()` is exactly `True`.

Telemetry must not collect scene contents, filenames, file paths, object names, scripts, Autodesk account information, OS usernames, hostnames, or other personal/project data.

Provider failures must never affect normal Script Toolbox behavior. Event delivery is best-effort and failures are swallowed by the telemetry facade/provider worker.

## Current PostHog provider

Official builds currently configure `PostHogProvider` for the EU ingestion host:

```text
https://eu.i.posthog.com
```

The public, write-only PostHog project token is not stored in git. GitHub Actions reads `POSTHOG_PROJECT_TOKEN` from repository secrets and stamps it into `telemetry/build_config.py` immediately before packaging Development and stable release artifacts.

Source checkouts keep `POSTHOG_PROJECT_TOKEN` blank, so telemetry transport is unavailable unless an official build stamped the configuration.

The provider uses PostHog's batch ingestion endpoint and sends in a background daemon thread so analytics does not block the DCC UI.

PostHog requires a `distinct_id` for events. Script Toolbox generates a random **process-scoped** id such as `stb-session-...`. It is not persisted between application sessions and is not derived from hardware, usernames, hostnames, account data, scenes, or project data.

Every event forces:

```text
$process_person_profile = false
```

so Script Toolbox telemetry does not create PostHog person profiles.

## Runtime bootstrap

`script_toolbox.bootstrap.show()` initializes telemetry before opening the UI. Runtime configuration combines:

- the build-time provider configuration;
- the persisted user consent value;
- a reviewed set of low-cardinality technical properties.

The first semantic event is:

```text
plugin_started
```

It is emitted at most once per loaded telemetry runtime and only when explicit consent is `True`.

The current common property allowlist is:

```text
plugin_version
build_channel
build_number
host
host_version
os
```

No filenames, paths, scene/object names, scripts, account information, usernames, or hostnames are included.

## Consent and Settings UI

When an official build has a telemetry transport configured and the stored consent value is `None`, Script Toolbox shows a first-run consent dialog after the runtime window opens.

The dialog presents two explicit choices:

- `Enable` stores `True`, enables the configured provider immediately, and allows the current runtime to emit `plugin_started`;
- `Don't Send` stores `False` and keeps telemetry disabled.

Closing the dialog without choosing either option leaves consent as `None`. The prompt is shown at most once per host process, so dismissing it does not repeatedly interrupt the same Maya/Nuke/Houdini session.

The main Script Toolbox header also exposes `Script Toolbox Settings`. Its Privacy section provides three states:

```text
Ask me next time
Enabled
Disabled
```

Changing this setting is applied immediately through `apply_telemetry_consent()`. The same Settings window also exposes the existing Stable/Development update-channel preference.

Source builds with no configured analytics transport do not show the first-run prompt. Their Privacy setting remains available and the consent choice is persisted for a later official build.

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

`NullTelemetryProvider` is always registered as `none` and is the default provider. Fresh source installs therefore have no active telemetry transport.

The null provider is also the safe fallback for tests, unavailable services, missing build configuration, and any build that does not configure an analytics backend.

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

This boundary supports PostHog now and a self-hosted/custom Script Toolbox analytics service later without coupling either backend to the rest of the plugin.
