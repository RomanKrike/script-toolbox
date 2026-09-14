# Architecture

Script Toolbox is a modular multi-DCC toolbox targeting Maya, Nuke and Houdini from a shared model/core.

## Compatibility targets

### Maya
- Maya 2015–2016 — Python 2.7-era hosts, PySide / Qt 4
- Maya 2017–2024 — PySide2 / Qt 5
- Maya 2025+ — PySide6 / Qt 6
- Python and MEL event scripts

### Nuke
- Nuke 12–15 — PySide2 / Qt 5
- Nuke 16+ — PySide6 / Qt 6
- Python event scripts

### Houdini
- Houdini 19–20.x standard Qt 5 builds — PySide2 / Qt 5
- Houdini 20.5 optional Qt 6 builds — PySide6 / Qt 6 when selected by the host
- Houdini 21 main builds — PySide6 / Qt 6; separate Qt 5.15.2 builds remain supported through PySide2
- Houdini 22+ — PySide6 / Qt 6; Qt 5 builds were dropped in Houdini 22
- Python and HScript event scripts

The shared UI is not forked per DCC generation. `qt_compat.py` resolves PySide / PySide2 / PySide6 at runtime, prefers a binding already loaded or selected by the host, mirrors Qt5/Qt6 `QtWidgets` onto the legacy `QtGui` widget surface, and supplies the small legacy API subset needed by the existing editor under Qt 6. This host-preference rule also covers Houdini 21 Qt 5 variant builds.

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
                 -> qt_compat

core/http_transport -> Python stdlib only
core/executor -> hosts
model -> pycompat (pure Python)
hosts/base -> Python stdlib only
hosts/maya_host -> maya.cmds / maya.mel
hosts/nuke_host -> nuke / nukescripts
hosts/houdini_host -> hou
qt_compat -> Python stdlib + selected PySide generation
```

The model layer must remain importable without Maya or Qt. Host-specific imports live behind `hosts/`, `compat.py`, and host integration modules. Qt binding selection and Qt4/Qt5/Qt6 API bridging belong in `qt_compat.py`; UI modules must not select PySide generations directly. `core/http_transport.py` is Qt/DCC-independent and must not import UI code.

## User config paths

`core/user_paths.py` is the single owner of runtime config/settings path resolution. Stable and Development builds use the same host-specific user config directory and the same canonical files. There is no separate test/dev runtime config path and no environment-variable override for config or settings files.

For Maya the canonical files are:

```text
<cmds.internalVar(userPrefDir=True)>/maya_script_toolbox.json
<cmds.internalVar(userPrefDir=True)>/script_toolbox_settings.json
```

Callers that need temporary locations for tests or import/export pass an explicit `path=` argument to the relevant config/preferences API; runtime path selection itself stays centralized.

## Current config schema

Schema **21** is the single supported configuration contract.

```text
JSON read
  -> validate schema version 21
  -> normalize current-schema Item envelopes and field values
  -> runtime document
```

A non-empty document without a version, an older schema, and a newer schema are all rejected. The config layer never infers, migrates or down-converts historical payloads. In particular, there is intentionally no schema 20 -> 21 migration. An empty mapping is used internally only to construct a brand-new current-schema document.

Breaking schema changes during development may advance `CONFIG_VERSION`, but the repository keeps only the current schema contract and current-schema tests unless backward compatibility is explicitly reintroduced as a product requirement.

## Universal Item model

Every persisted Item uses one stable envelope:

```json
{
  "kind": "integer",
  "id": "integer_samples",
  "name": "samples",
  "ui": {
    "label": "Samples",
    "show_label": true,
    "tooltip": "",
    "width_mode": "auto",
    "width": 120,
    "stretch": 1,
    "alignment": "left",
    "height_mode": "auto",
    "height": 28,
    "vertical_stretch": 1
  },
  "props": {
    "value": 8,
    "min": 1,
    "max": 64,
    "step": 1
  },
  "bindings": []
}
```

Containers add only `items`. Presentation/layout state belongs to `ui`; type-specific data belongs to `props`; event behavior belongs to `bindings`. Type-specific root keys are not a second persistence format.

`model/item_view.py` provides `ItemDataView`, a non-persisted adapter for existing runtime/property-editor code. It routes presentation keys to `ui` and type-specific keys to `props` while the serialized document remains schema 21 only.

Identity has one explicit contract:

- `id` is the canonical stable internal identifier and should be preferred for durable references;
- `name` is the supported symbolic identifier for scripts and human-readable API usage;
- `ui.label` is presentation text only and never participates in lookup.

Unknown kinds are rejected instead of silently converting to another type.

## Item type registry

`model/item_registry.py` is the authoritative extension point. A type is described by `ItemTypeDefinition`; core subsystems query the definition rather than maintaining parallel `kind` lists.

A definition owns:

- `kind`, `title`, `category`, `description`, `order`, `creatable`;
- typed `fields` for `props` normalization;
- public `events` and `internal_events`;
- semantic `capabilities` such as `container`, `layout`, `has_value`, `state_toggle`, `resizable` or `field_widget`;
- default UI metadata and default bindings;
- optional normalization hooks;
- `renderer_path` and `inspector_path` for lazy Qt-side resolution.

Built-ins live in `model/item_builtins.py`. Core routing no longer depends on `_FACTORIES`, `EVENT_CAPABILITIES`, `LAYOUT_KINDS`, `CONTAINER_KINDS`, `STATE_TOGGLE_KINDS` or a central property-editor map.

`ui/item_ui_bootstrap.py` is generic: it iterates `ITEM_TYPES`, resolves each definition's UI paths and binds the resulting renderer/inspector. `ui/runtime_renderers.py`, `ui/properties/registry.py`, bindings, values and palette logic consume the same registry metadata.

### Adding a new Item type

A new type should be registerable without editing central dispatch tables. For example, a Video type can declare its complete model/UI contract in one definition:

```python
from script_toolbox.model.fields import BoolField, PathField
from script_toolbox.model.item_registry import ItemTypeDefinition, register_item_type

register_item_type(ItemTypeDefinition(
    kind="video",
    title="Video",
    category="Display",
    fields={
        "source": PathField(default=""),
        "autoplay": BoolField(default=False),
    },
    events=("click", "double_click"),
    capabilities=("bindable", "resizable"),
    renderer_path=".video_item:render_video",
    inspector_path=".video_item:VideoPropertyEditor",
))
```

After registration, model construction and normalization recognize `video`; the Add Item palette derives its entry from registry metadata; runtime and Inspector binding resolve from the definition. Built-in `image` is the production proof of this pattern, and `tests/test_universal_item_extensibility.py` protects the same contract with a temporary Video type.

## Container and value contracts

Container semantics are definition-owned. Traversal, indexing, reference rewriting, cloning, topology and cache logic use registry capabilities and canonical `walk_items()` behavior rather than a maintained container-kind tuple.

`bindings` are the only persisted/runtime event mechanism. Callback dictionaries and direct script fields are not read or translated. A normal `button` is action-only. Stateful behavior belongs to `toggle_button` and `toggle_icon`, using the native `state_toggle` binding handler.

Toggle Button and Toggle Icon participate in the generic value API only when `state_source == "internal"`. Script-driven toggles do not persist or acquire a synthetic `props.value` through `store_value()`.

Numeric scalar/vector construction and runtime writes share definition normalizers so size, min/max clamping, component count and fallback behavior cannot diverge. Field values preserve the established runtime contract: scalar values become text, list/tuple values become lists of text values, and single-value fields collapse list input to the first value.

For Icon and Toggle Icon alignment, `content_alignment` is the only type-specific property key. Generic layout alignment belongs to `ui.alignment`.

## Editor architecture

`EditorDocumentController` owns the staged document, identity cache, clone/reference operations and topology. It is Qt-independent.

The active Interface Editor composes controller ownership, command history, Row/Column tree helpers, search presentation, sharing and view-state preservation through `ui/editor_document_adapter.py`.

`ui/layout_editor_adapter.py` contains helper functions only; it does not publish a second editor wrapper class or separate layout document controller. A small marker on the active document adapter exists solely to prevent duplicate wrapping during development hot reload.

The Add Item palette is populated from `ITEM_TYPES.creatable()` metadata through `ui/item_palette.py`; built-in type metadata, not editor command code, is the authoritative catalog.

## UI composition lifecycle

`ui/bootstrap.py` is the UI/runtime composition root. It owns ordered construction of the final `InterfaceEditor` and `ScriptToolbox` classes and installs generic registry-driven UI/runtime adapters.

`ui/__init__.py` is intentionally declarative. For backward compatibility, importing `script_toolbox.ui` still initializes the complete UI automatically, but package import contains one visible composition call:

```python
_RUNTIME = initialize_ui()
```

The resulting `UIComposition` contains the final public classes and the active runtime renderer registry. `from script_toolbox.ui import ScriptToolbox` and `from script_toolbox.ui import InterfaceEditor` therefore keep their existing public contract.

`initialize_ui()` is idempotent within one loaded module graph: a completed composition is cached and returned on repeated calls. A failed composition is not cached, so a later retry can recover. Hook modules retain only the markers that are still needed to prevent duplicate wrapping, event filters or method replacement.

For development hot reload, bootstrap reuses the active renderer registry when the runtime module object has not changed. This preserves third-party renderer registrations and existing registry-owned install markers if only the composition module is reloaded. When `ui.runtime` itself is reloaded, bootstrap creates a fresh default registry for the new runtime classes.

The remaining assignment of the telemetry-aware share installer into `editor_document_adapter` is a deliberately contained transitional compatibility monkeypatch. It is centralized in the composition root instead of being spread across package import code; removing that adapter-global dependency is deferred until it can be done without breaking direct builder imports.

## Runtime rendering

`RuntimeFolder.build_runtime_widget()` routes through the runtime renderer registry directly. The registry lifecycle is owned by UI bootstrap. Runtime renderer registration is derived from `ItemTypeDefinition.renderer` after generic UI path resolution; adding a new type does not require editing a renderer switch/table.

Runtime event filters attach only events declared by the Item definition and dispatch through `bindings`. Renderer-specific modules do not patch main-window event semantics.

Runtime value synchronization is capability-driven. Ordinary `has_value` Items register a `RuntimeValueBinding`; specialized field refresh uses the `field_widget` capability instead of a `kind == "field"` branch.

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

- `qt_compat.py`, which owns PySide generation selection, the legacy QtGui widget surface, and the Qt 6 compatibility subset used by the editor;
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
  qt_compat.py
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
    fields.py
    index.py
    item_builtins.py
    item_registry.py
    item_view.py
    items.py
    layouts.py

  style/
    ...

  ui/
    __init__.py
    bootstrap.py
    item_palette.py
    item_ui_bootstrap.py
    image_item.py
    main_window.py
    debounced_main_window.py
    runtime.py
    runtime_renderers.py
    runtime_value_sync.py
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
      text.py
      separator.py
```

## Rules

- No circular imports.
- No DCC UI/API code in `model`.
- Host-specific API access belongs in `hosts/` or host integration modules.
- No JSON file I/O in `ui`.
- Runtime config/settings paths are owned only by `core/user_paths.py`.
- Stable and Development builds share the same canonical user config files.
- Only the current config schema is supported while the project remains in development.
- Persist Items only in the schema 21 envelope; do not add type-specific root keys as a compatibility layer.
- Never silently convert an unknown item kind to another kind.
- Never use `ui.label` as item identity.
- Persist event behavior only as `bindings`.
- New item types register through `ItemTypeDefinition`; core, palette, events, runtime and Inspector routing must derive from that metadata instead of central kind tables.
- Structural recursion uses registry container capabilities and canonical traversal.
- Shared network compatibility belongs in `core/http_transport.py`; updater/share must not duplicate PowerShell transport logic.
- Qt binding selection and Qt4/Qt5/Qt6 compatibility belong in `qt_compat.py`; host/UI modules must not create parallel binding logic.
- UI/runtime composition ordering belongs in `ui/bootstrap.py`; `ui/__init__.py` should remain a small public export surface.
- Source remains Python 2.7 compatible until support for the legacy Maya 2015 / Nuke 12 generation is intentionally dropped.
