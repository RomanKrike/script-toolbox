# Telemetry event catalog

This file is the public allowlist of semantic product events that Script Toolbox may send after explicit telemetry consent.

All events also receive the reviewed common technical properties from the telemetry runtime:

```text
plugin_version
build_channel
build_number
host
host_version
os
```

No event in this catalog may include scene contents, filenames, file paths, object names, item labels/names, scripts, Autodesk account information, OS usernames, hostnames, config contents, or other arbitrary user-controlled strings.

## Product events

Telemetry is intentionally sparse. We collect durable product actions rather than UI interaction noise.

| Event | Event-specific properties | Meaning |
| --- | --- | --- |
| `plugin_started` | none | One Script Toolbox telemetry runtime started. |
| `item_created` | `item_type` | A parameter/layout item was created from the editor palette. |
| `item_duplicated` | `item_type` | An existing item/subtree was duplicated. |
| `config_imported` | `mode` | A JSON toolbox import completed successfully. |
| `config_exported` | none | A JSON toolbox export completed successfully. |
| `share_created` | `share_type` | An encrypted share operation completed successfully and produced an STB1 code. |
| `share_pasted` | `share_type` | Shared data was downloaded, decrypted and inserted into the editor. |

The following high-frequency or low-value UI interactions are deliberately not tracked:

```text
editor_opened
settings_opened
item_activated
```

## Property enums

`item_type` is normalized to a fixed low-cardinality enum. Current values include:

```text
button
checkbox
color
column
field
float
folder
icon
integer
label
menu
row
separator
string
text
toggle_button
toggle_icon
other
```

Unknown future item kinds become `other` instead of sending their raw value.

`config_imported.mode` is one of:

```text
replace
append
insert
```

`share_type` is one of:

```text
config
item
```

## Fail-closed event gate

Product instrumentation uses `track_product_event()`. The event gate rejects:

- unknown event names;
- unknown property names;
- non-dictionary property payloads;
- property values outside the reviewed enum for that event.

For item kinds only, an unknown kind is reduced to the literal `other` value. This lets future item types remain measurable without sending an arbitrary string.

The low-level provider facade still exists for telemetry infrastructure, but product/UI code should use the reviewed event gate.
