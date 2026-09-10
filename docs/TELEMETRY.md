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

After explicit opt-in, Script Toolbox creates a random pseudonymous installation identifier. It is not derived from hardware, usernames, hostnames, Autodesk/account data, scenes, projects, or filesystem data. It is stored in the local Script Toolbox preferences and reused across application sessions so aggregate unique-install and retention metrics remain meaningful.

Telemetry must not collect scene contents, filenames, file paths, object names, scripts, Autodesk account information, OS usernames, hostnames, hardware identifiers, or other personal/project data.

Provider failures must never affect normal Script Toolbox behavior. Event delivery is best-effort and failures are swallowed by the telemetry facade/provider worker.

## Current PostHog provider

Official builds currently configure `PostHogProvider` for the EU ingestion host:

```text
https://eu.i.posthog.com
```

The public, write-only PostHog project token is not stored in git. GitHub Actions reads `POSTHOG_PROJECT_TOKEN` from repository secrets and stamps it into `telemetry/build_config.py` immediately before packaging Development and stable release artifacts.

Source checkouts keep `POSTHOG_PROJECT_TOKEN` blank, so telemetry transport is unavailable unless an official build stamped the configuration.

The provider uses PostHog's batch ingestion endpoint and sends in a background daemon thread so analytics does not block the DCC UI.

PostHog requires a `distinct_id` for events. In official telemetry-enabled runtime, Script Toolbox uses the persisted random installation id:

```text
stb-install-<random uuid>
```

The id is created only when both a telemetry transport is configured and the user has explicitly opted in. It is reused across Maya/Nuke/Houdini application sessions on that installation. If no persisted installation id can be stored, telemetry remains disabled rather than silently falling back to a new identity on every process.

Every event forces:

```text
$process_person_profile = false
```

so Script Toolbox telemetry does not create PostHog person profiles. The persistent random `distinct_id` is used only to count the same installation consistently across sessions.

## Runtime bootstrap

`script_toolbox.bootstrap.show()` initializes telemetry before opening the UI. Runtime configuration combines:

- the build-time provider configuration;
- the persisted user consent value;
- the persisted random installation id after consent;
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

No filenames, paths, scene/object names, scripts, account information, usernames, hostnames, or hardware identifiers are included.

## Consent and Settings UI

When an official build has a telemetry transport configured and the stored consent value is `None`, Script Toolbox shows a first-run consent dialog after the runtime window opens.

The dialog presents two explicit choices:

- `Enable` stores `True`, creates/reuses the random installation id, enables the configured provider immediately, and allows the current runtime to emit `plugin_started`;
- `Don't Send` stores `False` and keeps telemetry disabled.

Closing the dialog without choosing either option leaves consent as `None`. The prompt is shown at most once per host process, so dismissing it does not repeatedly interrupt the same Maya/Nuke/Houdini session.

The main Script Toolbox header also exposes `Script Toolbox Settings`. Its Privacy section provides three states:

```text
Ask me next time
Enabled
Disabled
```

Changing this setting is applied immediately through `apply_telemetry_consent()`. Disabling telemetry stops event delivery but does not delete the locally stored random installation id; re-enabling therefore resumes the same pseudonymous installation identity. The same Settings window also exposes the existing Stable/Development update-channel preference.

Source builds with no configured analytics transport do not show the first-run prompt. Their Privacy setting remains available and the consent choice is persisted for a later official build. A telemetry installation id is not created until an actual transport is available.

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

Feature code remains backend-independent and goes through the reviewed product-event gate:

```python
from script_toolbox import telemetry

telemetry.track_product_event(
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

The user's persisted privacy state contains consent plus, after opt-in, the random installation identifier. It does not contain a provider selection.

## Event design

Telemetry is intentionally sparse. Product events represent durable actions rather than UI traffic. The current semantic event set is:

```text
plugin_started
item_created
item_duplicated
config_imported
config_exported
share_created
share_pasted
```

We deliberately do not track editor/settings opens or runtime item clicks. Those interactions created unnecessary event volume without enough product value.

Event-specific properties are restricted to low-cardinality enums such as:

```text
item_type
mode
share_type
```

Product/UI code uses `track_product_event()`, which rejects unknown event names, unknown property keys and unapproved enum values before they can reach a provider. Unknown future item kinds are reduced to the literal `other` value rather than sending their raw name.

The complete public event/property allowlist is documented in [`TELEMETRY_EVENTS.md`](TELEMETRY_EVENTS.md).

Do not send arbitrary strings originating from user scenes, scripts, paths, labels, object names, item names, filenames or config content.

## Switching providers

A provider switch should follow this sequence:

1. Implement a new `TelemetryProvider`.
2. Add provider-specific tests.
3. Register it during bootstrap.
4. Select it in `telemetry.configure(...)`.
5. Keep the event schema stable unless a product requirement explicitly changes it.

The persisted random installation id is provider-independent and should be reused by future analytics backends when the user's consent remains enabled. This boundary supports PostHog now and a self-hosted/custom Script Toolbox analytics service later without coupling either backend to the rest of the plugin.
