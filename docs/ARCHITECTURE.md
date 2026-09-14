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

Every persisted and in-memory document Item uses one stable envelope:

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

Containers add only `items`. Presentation/layout state belongs to `ui`; type-specific data belongs to `props`; event behavior belongs to `bindings`. Runtime and Inspector code read these namespaces explicitly. There is no flat Item compatibility view and no second in-memory Item format.

Identity has one explicit contract:

- `id` is the canonical stable internal identifier and should be preferred for durable references;
- `name` is the supported symbolic identifier for scripts and human-readable API usage;
- `ui.label` is presentation text only and never participates in lookup.

Unknown kinds are rejected instead of silently converting to another type. `kind` is the only Item type discriminator; there is no parallel `type` field.

## Item type registry

`model/item_registry.py` is the authoritative extension point. A type is described by `ItemTypeDefinition`; core subsystems query the definition rather than maintaining parallel `kind` lists.

A definition owns:

- `kind`, `title`, `category`, `description`, `order`, `creatable`;
- typed `fields` for `props` normalization;
- public `events` and `internal_events`;
- semantic `capabilities` such as `container`, `layout`, `section`, `has_value`, `state_toggle`, `resizable`, `field_widget`, `native_button` or `divider`;
- default UI metadata and default bindings;
- optional `normalize_props` hook for cross-field invariants;
- `renderer_path` and `inspector_path` for lazy Qt-side resolution.

`layout_axis` is derived from a layout definition's schema metadata, so generic editor/layout code does not need to identify Row or Column by name.

Core routing no longer depends on `_FACTORIES`, `EVENT_CAPABILITIES`, `LAYOUT_KINDS`, `CONTAINER_KINDS`, `STATE_TOGGLE_KINDS`, a central property-editor map, a renderer switch, or an authored palette kind list.

Standard built-ins are registered by `model/item_builtins.py`. Independently extensible built-ins live under `model/item_definitions/`; `Image` is defined in `model/item_definitions/image.py` and is included by the explicit built-in definition bootstrap. This keeps import order obvious and Python 2/Maya 2015 friendly while allowing a new built-in type to be added as a type-specific module plus one bootstrap entry.

`ui/item_ui_bootstrap.py` is generic: it iterates `ITEM_TYPES`, resolves each definition's UI paths and binds the resulting renderer/inspector. `ui/runtime_renderers.py`, `ui/properties/registry.py`, bindings, values, Interface Editor containment and palette logic consume the same registry metadata.

## Field schema

The model provides declarative field definitions including `TextField`, `BoolField`, `IntField`, `FloatField`, `ChoiceField`, `ColorField`, `PathField` and `ListField`.

Fields own defaults and value-level normalization. Numeric fields may clamp to minimum/maximum bounds; choice fields validate against declared choices; list fields can normalize their members through another Field.

Complex invariants stay at Item-definition level through `normalize_props`. The normalization pipeline is:

```text
raw props
  -> per-field normalization
  -> ItemTypeDefinition.normalize_props hook
  -> normalized props
```

This is used for numeric vector size/range invariants, Menu values, Field display semantics and state-toggle storage behavior.

## Adding a new Item type

Add the type-specific implementation; do not edit routing core.

For a built-in `video`:

1. add `model/item_definitions/video.py` with its `ItemTypeDefinition`;
2. add its renderer and Inspector modules/classes;
3. include `video_definition()` in the explicit `model/item_definitions/__init__.py` bootstrap tuple;
4. add tests.

Example definition:

```python
from script_toolbox.model.fields import BoolField, ChoiceField, PathField
from script_toolbox.model.item_registry import ItemTypeDefinition


def video_definition():
    return ItemTypeDefinition(
        kind="video",
        title="Video",
        category="Display",
        fields={
            "source": PathField(default=""),
            "autoplay": BoolField(default=False),
            "loop": BoolField(default=False),
            "fit": ChoiceField(
                ("contain", "cover", "stretch"),
                default="contain"
            ),
        },
        events=("click", "double_click"),
        capabilities=("bindable", "resizable"),
        renderer_path=".video_item:render_video",
        inspector_path=".video_item:VideoPropertyEditor",
    )
```

No change is required in `bindings.py`, `layouts.py`, runtime dispatch, the property registry, `interface_editor.py`, `item_palette.py`, or document normalization. External/future plugin code can instead call `register_item_type()` directly and does not need the built-in bootstrap entry.

Built-in `Image` is the production proof of this pattern. It defines only `source`, `fit`, `width`, `height`; supports `contain`, `cover`, `stretch`; declares `click`/`double_click`; and supplies its renderer and specialized Inspector through its definition metadata.

## Container and value contracts

Container semantics are definition-owned. Traversal, indexing, reference rewriting, cloning, topology and editor containment use registry capabilities and canonical `walk_items()` behavior rather than a maintained container-kind tuple.

Top-level document sections are expressed by the `section` capability. Layout containers use `layout`; generic editor rules prevent a layout from owning a section without knowing any concrete kind name.

`bindings` are the only persisted/runtime event mechanism. Callback dictionaries and direct script fields are not read or translated. A normal `button` is action-only. Stateful behavior belongs to definitions with `state_toggle`; button chrome is selected through `native_button` rather than concrete kind checks.

Toggle Button and Toggle Icon participate in the generic value API only when `state_source == "internal"`. Script-driven toggles do not persist or acquire a synthetic `props.value` through `store_value()`.

Numeric scalar/vector construction and runtime writes share definition normalizers so size, min/max clamping, component count and fallback behavior cannot diverge. Field values preserve the established runtime contract: scalar values become text, list/tuple values become lists of text values, and single-value fields collapse list input to the first value.

For Icon and Toggle Icon alignment, `content_alignment` is the only type-specific property key. Generic layout alignment belongs to `ui.alignment`.

## Editor architecture

`EditorDocumentController` owns the staged document, identity cache, clone/reference operations and topology. It is Qt-independent.

The base Interface Editor itself uses the registry for palette entries, type titles, container/section semantics and tree structure. `ui/layout_editor_adapter.py` contains reusable capability-driven tree helpers; it does not contain a second list of Folder/Row/Column kinds.

`ui/editor_document_adapter.py` composes controller ownership, command history, search presentation, sharing and view-state preservation around that registry-driven editor. Layout routing no longer requires an adapter-specific kind switch.

The Add Item palette is generated from `ITEM_TYPES.creatable()` metadata each time the editor UI is built. Categories are derived from definition metadata, so a newly registered category appears without editing the Interface Editor.

## UI composition lifecycle

`ui/bootstrap.py` is the UI/runtime composition root. It owns ordered construction of the final `InterfaceEditor` and `ScriptToolbox` classes and installs generic registry-driven UI/runtime hooks.

`ui/__init__.py` is intentionally declarative. Importing `script_toolbox.ui` initializes the complete UI automatically through one visible composition call:

```python
_RUNTIME = initialize_ui()
```

The resulting `UIComposition` contains the final public classes and the active runtime renderer registry. `from script_toolbox.ui import ScriptToolbox` and `from script_toolbox.ui import InterfaceEditor` therefore keep their public contract.

`initialize_ui()` is idempotent within one loaded module graph: a completed composition is cached and returned on repeated calls. A failed composition is not cached, so a later retry can recover. Hook modules retain only markers needed to prevent duplicate wrapping, event filters or method replacement during development hot reload.

For development hot reload, bootstrap reuses the active renderer registry when the runtime module object has not changed. When `ui.runtime` itself is reloaded, bootstrap creates a fresh default registry for the new runtime classes.

The telemetry-aware share installer assignment into `editor_document_adapter` is unrelated to Item serialization/type routing; it remains centralized in the UI composition root.

## Runtime rendering

`RuntimeFolder.build_runtime_widget()` routes through the runtime renderer registry directly. The registry lifecycle is owned by UI bootstrap. Runtime renderer registration is derived from `ItemTypeDefinition.renderer` after generic UI path resolution; adding a new type does not require editing a renderer switch/table.

All runtime renderers receive the raw universal Item envelope and read `ui` and `props` explicitly. `core/runtime_registry.py` has no Item-shape adapter.

Runtime event filters attach only events declared by the Item definition and dispatch through `bindings`. Renderer-specific modules do not patch main-window event semantics.

Runtime value synchronization is capability-driven. Ordinary `has_value` Items register a `RuntimeValueBinding`; specialized field refresh uses the `field_widget` capability instead of a `kind == "field"` branch.

Stateful execution and refresh use capabilities and definition fields. Toggle renderers only create/register their widgets; state semantics do not depend on `toggle_button`/`toggle_icon` name checks.

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

The Item architecture intentionally has no compatibility layer for pre-v21 Item shapes: no flat Item view, no schema 20 -> 21 migration, no dual registry and no legacy factory routing.

Compatibility code for unrelated product/platform concerns remains allowed where it is part of the supported runtime contract, for example:

- `qt_compat.py` for PySide generation selection and Qt API bridging;
- updater/share transport forwarding required by legacy Windows/Python hosts;
- documented host-integration compatibility surfaces.

These unrelated compatibility layers must not become an alternate Item data/type architecture.

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
    items.py
    layouts.py
    item_definitions/
      __init__.py
      image.py

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
- Persist and operate on Items only through the schema 21 envelope; do not add type-specific root keys or a flat compatibility view.
- Never silently convert an unknown item kind to another kind.
- Never use `ui.label` as item identity.
- Persist event behavior only as `bindings`.
- New item types register through `ItemTypeDefinition`; core, palette, events, runtime and Inspector routing must derive from that metadata instead of central kind tables.
- Structural recursion and editor containment use registry capabilities and canonical traversal.
- Shared network compatibility belongs in `core/http_transport.py`; updater/share must not duplicate PowerShell transport logic.
- Qt binding selection and Qt4/Qt5/Qt6 compatibility belong in `qt_compat.py`; host/UI modules must not create parallel binding logic.
- UI/runtime composition ordering belongs in `ui/bootstrap.py`; `ui/__init__.py` should remain a small public export surface.
- Source remains Python 2.7 compatible until support for the legacy Maya 2015 / Nuke 12 generation is intentionally dropped.
