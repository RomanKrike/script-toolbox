# Architecture

Script Toolbox is a modular multi-DCC toolbox targeting Maya, Nuke and Houdini from a shared model/core.

## Compatibility targets

### Maya
- Autodesk Maya 2015
- Python 2.7
- PySide 1 / Qt 4
- Python and MEL event scripts

### Nuke
- Nuke 12
- Python 2.7
- PySide2 / Qt 5
- Python event scripts

### Houdini
- Houdini 19.0
- Python 3.7 default build
- PySide2 / Qt 5
- Python and HScript event scripts

Historical Script Toolbox config schemas are intentionally **not** a compatibility target while the plugin remains under active development.

## Dependency direction

```text
model -> core -> hosts -> ui

ui/main_window -> ui/runtime -> core/values -> model
      |               |
      |               -> style
      |
      -> core/config -> core/config_schema
      -> core/user_paths -> hosts
      -> core/event_bindings -> core/executor
      -> compat -> hosts

core/http_transport -> Python stdlib only
core/executor -> hosts
model -> pycompat (pure Python)
hosts/base -> Python stdlib only
hosts/maya_host -> maya.cmds / maya.mel
hosts/nuke_host -> nuke / nukescripts
hosts/houdini_host -> hou
```

The model layer must remain importable without Maya or Qt. Host-specific imports live behind `hosts/`, `compat.py`, and host integration modules. `core/http_transport.py` is Qt/DCC-independent and must not import UI code.

## User config paths

`core/user_paths.py` is the single owner of runtime config/settings path resolution. Stable and Development builds use the same host-specific user config directory and the same canonical files. There is no separate test/dev runtime config path and no environment-variable override for config or settings files.

For Maya the canonical files are:

```text
<cmds.internalVar(userPrefDir=True)>/maya_script_toolbox.json
<cmds.internalVar(userPrefDir=True)>/script_toolbox_settings.json
```

Callers that need temporary locations for tests or import/export pass an explicit `path=` argument to the relevant config/preferences API; runtime path selection itself stays centralized.

## Current config schema

Schema **20** is the single supported configuration contract.

```text
JSON read
  -> validate schema version 20
  -> normalize current-schema values/defaults
  -> runtime document
```

A non-empty document without a version, an older schema, and a newer schema are all rejected. The config layer never infers, migrates or down-converts historical payloads. An empty mapping is used internally only to construct a brand-new current-schema document.

Breaking schema changes during development may advance `CONFIG_VERSION`, but the repository keeps only the current schema contract and current-schema tests unless backward compatibility is explicitly reintroduced as a product requirement.

## Item model contracts

Container semantics are model-owned. `folder`, `row`, and `column` are the canonical container kinds; document traversal, indexing, reference rewriting, cloning, topology and cache logic use the shared container predicate and canonical `walk_items()` implementation.

Item construction is owned by the model factory registry. `button`, `toggle_button`, `icon`, `toggle_icon`, value controls, `row`, `column`, and `folder` are native item kinds. Unknown kinds are rejected instead of silently converting to another type.

Identity has one explicit contract:

- `id` is the canonical stable internal identifier and should be preferred for durable references;
- `name` is the supported symbolic identifier for scripts and human-readable API usage;
- `label` is presentation text only and never participates in lookup.

`bindings` are the only persisted/runtime event mechanism. Callback dictionaries and direct script fields are not read or translated. A normal `button` is action-only. Stateful behavior belongs to `toggle_button` and `toggle_icon`, using the native `state_toggle` binding handler.

For Icon and Toggle Icon alignment, `content_alignment` is the only schema key. `alignment` is not an alias.

Numeric scalar/vector construction and runtime writes share one normalizer so size, min/max clamping, component count and fallback behavior cannot diverge.

## Editor architecture

`EditorDocumentController` owns the staged document, identity cache, clone/reference operations and topology. It is Qt-independent.

The active Interface Editor composes controller ownership, command history, Row/Column tree helpers, search presentation, sharing and view-state preservation through `ui/editor_document_adapter.py`.

`ui/layout_editor_adapter.py` contains helper functions only; it does not publish a second editor wrapper class or separate layout document controller. A small marker on the active document adapter exists solely to prevent duplicate wrapping during development hot reload.

## UI composition lifecycle

`ui/bootstrap.py` is the UI/runtime composition root. It owns the ordered construction of the final `InterfaceEditor` and `ScriptToolbox` classes, runtime renderer setup and the remaining compatibility hook installation.

`ui/__init__.py` is intentionally declarative. For backward compatibility, importing `script_toolbox.ui` still initializes the complete UI automatically, but package import now contains one visible composition call:

```python
_RUNTIME = initialize_ui()
```

The resulting `UIComposition` contains the final public classes and the active runtime renderer registry. `from script_toolbox.ui import ScriptToolbox` and `from script_toolbox.ui import InterfaceEditor` therefore keep their existing public contract.

`initialize_ui()` is idempotent within one loaded module graph: a completed composition is cached and returned on repeated calls. A failed composition is not cached, so a later retry can recover. Hook modules retain only the markers that are still needed to prevent duplicate wrapping, event filters or method replacement.

For development hot reload, bootstrap reuses the active renderer registry when the runtime module object has not changed. This preserves third-party renderer registrations and existing registry-owned install markers if only the composition module is reloaded. When `ui.runtime` itself is reloaded, bootstrap creates a fresh default registry for the new runtime classes. Built-in renderer registration uses explicit replacement, so repeated composition cannot accumulate duplicate built-ins.

The remaining assignment of the telemetry-aware share installer into `editor_document_adapter` is a deliberately contained transitional compatibility monkeypatch. It is centralized in the composition root instead of being spread across package import code; removing that adapter-global dependency is deferred until it can be done without breaking direct builder imports.

## Runtime rendering

`RuntimeFolder.build_runtime_widget()` routes through the runtime renderer registry directly. The registry lifecycle is owned by UI bootstrap. Base renderers are initialized once for the active runtime module and specialized current kinds are registered explicitly by the composition root.

Runtime event filters attach supported mouse/editing/selection events to rendered widgets and dispatch through `bindings`. Renderer-specific modules do not patch main-window event semantics.

Stateful execution and refresh are owned by the main runtime API. Toggle Button and Toggle Icon renderers only create and register their widgets.

## Network transport

`core/http_transport.py` is the single low-level HTTP transport used by both updater and sharing. Callers provide URL, payload, headers and timeout and receive bytes/file output or a `TransportError`; they do not need to know about `urllib`, subprocesses, TLS setup or PowerShell command construction.

Transport policy is:

- non-Windows: Python `urllib` only;
- modern Windows/Python: `urllib` first, then PowerShell/.NET fallback on transport failure;
- legacy Windows/Python 2: PowerShell/.NET first because the host Python HTTPS stack can lack modern TLS/certificate/SNI behavior, then `urllib` fallback if PowerShell fails;
- after a successful need for PowerShell fallback on modern Windows, that process prefers PowerShell for later shared transport calls.

PowerShell requests use .NET `HttpWebRequest`, TLS 1.2, hidden-process startup flags and explicit request/read-write timeouts. Authorization is passed to the child through a temporary environment variable rather than embedded in the command line. Request bodies and response downloads use temporary/binary files where needed so updater and sharing do not maintain separate PowerShell implementations.

`core.updater` translates transport failures into `UpdateError`; `share.provider` translates them into `ShareProviderError`.

## Compatibility policy

Compatibility symbols are classified by whether they are internal dead code or externally importable API. Internal duplicate implementations may be removed after repository-wide usage checks. Potentially externally imported symbols are kept as small forwarding/no-op shims until an intentional breaking change.

Current compatibility layers include:

- updater private transport helpers such as `_download_with_powershell`, which now forward to `core.http_transport`;
- share provider private Windows/PowerShell helpers, which also forward to `core.http_transport`;
- `ui/icon_ui_hooks.py`, retained as documented no-op shims for older direct imports;
- selected base `InterfaceEditor` methods that are overridden by the production adapter chain but may still be reached through direct module imports;
- `install_runtime_folder_chrome`, retained as a forwarding compatibility alias.

These compatibility layers must not grow independent implementations. New production flow should use the canonical APIs directly.

## Current package layout

```text
scripts/script_toolbox/
  __init__.py
  bootstrap.py
  compat.py
  pycompat.py
  constants.py
  nuke_integration.py
  houdini_integration.py

  hosts/
    base.py
    maya_host.py
    nuke_host.py
    houdini_host.py

  core/
    config.py
    config_schema.py
    user_paths.py
    editor_commands.py
    editor_document.py
    event_bindings.py
    executor.py
    http_transport.py
    references.py
    runtime_registry.py
    values.py
    updater.py

  model/
    __init__.py
    bindings.py
    index.py
    items.py
    layouts.py

  style/
    ...

  ui/
    __init__.py
    bootstrap.py
    main_window.py
    debounced_main_window.py
    runtime.py
    runtime_renderers.py
    editor_document_adapter.py
    layout_editor_adapter.py
    ...

    properties/
      base.py
      registry.py
      folder.py
      row.py
      column.py
      basic.py
      field.py
      button.py
      toggle_button.py
      icon.py
      toggle_icon.py
```

## Rules

- No circular imports.
- No DCC UI/API code in `model`.
- Host-specific API access belongs in `hosts/` or host integration modules.
- No JSON file I/O in `ui`.
- Runtime config/settings paths are owned only by `core/user_paths.py`.
- Stable and Development builds share the same canonical user config files.
- Only the current config schema is supported while the project remains in development.
- Never silently convert an unknown item kind to another kind.
- Never use `label` as item identity.
- Persist event behavior only as `bindings`.
- Persist icon alignment only as `content_alignment`.
- New item types register through model, renderer and property-editor registries.
- Structural recursion uses the shared container predicate.
- Shared network compatibility belongs in `core/http_transport.py`; updater/share must not duplicate PowerShell transport logic.
- UI/runtime composition ordering belongs in `ui/bootstrap.py`; `ui/__init__.py` should remain a small public export surface.
- Source remains Python 2.7 compatible until Maya 2015 support is intentionally dropped.
