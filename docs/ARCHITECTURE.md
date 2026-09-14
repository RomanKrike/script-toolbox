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
  -> normalize and validate current-schema Item envelopes/props
  -> runtime document
```

Config version validation and Item validation are separate layers. A non-empty document without a version, an older schema, and a newer schema are rejected by `core/config_schema.py` before Item normalization. Current-schema Items are then constructed through the model schema. Malformed typed props are not silently replaced with unrelated defaults. In particular, there is intentionally no schema 20 -> 21 migration. An empty mapping is used internally only to construct a brand-new current-schema document.

Breaking schema changes during development may advance `CONFIG_VERSION`, but these architecture changes do not modify the persisted envelope, so the current schema remains 21.

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

Unknown kinds are rejected instead of silently converting to another type. `kind` is the only Item type discriminator; there is no parallel `type` field, `UnknownItem`, `RawItem`, or placeholder compatibility storage.

## Item type registry

`model/item_registry.py` is the authoritative extension point. A type is described by `ItemTypeDefinition`; core subsystems query the definition rather than maintaining parallel `kind` lists.

A definition owns:

- `kind`, `title`, `category`, `description`, `order`, `creatable`;
- typed `fields` for the `props` data contract;
- public `events` and `internal_events`;
- semantic `capabilities` such as `container`, `layout`, `section`, `has_value`, `state_toggle`, `resizable`, `field_widget`, `native_button` or `divider`;
- optional `LayoutSpec` and `SectionSpec` semantic metadata;
- default UI metadata and default bindings;
- optional `normalize_props` hook for cross-field invariants;
- `renderer_path` and `inspector_path` for lazy Qt-side resolution.

Capabilities remain the authoritative semantic flags. Convenience properties such as `definition.is_layout`, `definition.is_section`, `definition.layout_spec` and `definition.section_spec` make generic consumers explicit without introducing a type hierarchy.

Core routing no longer depends on `_FACTORIES`, `EVENT_CAPABILITIES`, `LAYOUT_KINDS`, `CONTAINER_KINDS`, `FOLDER_TYPES`, `STATE_TOGGLE_KINDS`, a central property-editor map, a renderer switch, or an authored palette kind list.

Standard built-ins are registered by `model/item_builtins.py`. Their `ItemTypeDefinition`/Field objects are lazily constructed once per loaded `item_builtins` module graph and reused by repeated `register_builtin_items()` calls. This avoids rebuilding schemas on every lookup without adding a second registry. Reloading the module resets that cache naturally; `ITEM_TYPES` remains authoritative about which definitions are currently registered.

Independently extensible built-ins live under `model/item_definitions/`; `Image` is defined in `model/item_definitions/image.py` and is included by the explicit built-in definition bootstrap. A new built-in therefore requires only its type-specific module plus, at most, one explicit bootstrap entry.

`ui/item_ui_bootstrap.py` is generic and re-entrant: it iterates the current `ITEM_TYPES`, resolves unresolved UI paths and binds the resulting renderer/Inspector. `ui/runtime_renderers.py`, `ui/properties/registry.py`, bindings, values, Interface Editor containment and palette logic consume the same registry metadata.

## Field schema and validation pipeline

The model provides declarative field definitions including `TextField`, `BoolField`, `IntField`, `FloatField`, `ChoiceField`, `ColorField`, `PathField` and `ListField`. Field classes remain model-only and do not map themselves to Qt controls.

Fields own defaults, supported coercion/parsing, value normalization and value validation. The production `props` pipeline is:

```text
raw props
  -> field parsing / supported coercion
  -> field normalization (including numeric bounds)
  -> per-field validation
  -> ItemTypeDefinition.normalize_props cross-field hook
  -> final field validation
  -> canonical props
```

`ItemTypeDefinition.validate_props()` uses the same supported coercion rules for diagnostic validation. Canonical construction, `normalize_document()`, editor writes through `normalize_item_props()`, config load and runtime value writes all use `ItemTypeDefinition.normalize_props()`; validation is therefore part of the real data path rather than an optional helper.

The coercion boundary is explicit:

- `IntField`: `"12"` may coerce to `12`; `"hello"` is invalid rather than becoming a default.
- `FloatField`: numeric text may coerce; unrelated text is invalid.
- `ChoiceField`: case-insensitive text may resolve to one declared choice; an undeclared choice is invalid.
- `BoolField`: accepts booleans, `1`/`0`, and the explicit case-insensitive strings `true`/`false`, `yes`/`no`, `1`/`0`; arbitrary non-empty strings are invalid. In particular, `BoolField.normalize("false")` is `False`, never Python's `bool("false") == True` behavior.
- numeric/color bounds normalize by clamping after successful parsing; parsing failure is not a bound case and raises validation error.

`FieldValidationError` describes a field-level parse/validation failure. `ItemValidationError` is the Item-level error contract and carries `kind`, optional `id`/`name`, `field`, bad `value`, and `reason`. Config recovery surfaces that structured message for malformed current-schema data instead of silently repairing it.

Complex cross-field invariants stay at definition level through `normalize_props`; the Inspector does not become a second validator. Specialized editors may write raw UI values into `props`, but `PropertyEditorBase.write_to_item()` then calls `normalize_item_props()` before emitting the changed state.

## Layout semantics

Layout behavior is explicit metadata, not an inference from field names. A layout definition declares capability `layout` and a `LayoutSpec`:

```python
LayoutSpec(
    axis="horizontal",
    distribution_field="distribution",
    cross_alignment_field="cross_alignment",
    equal_size_field="equal_sizes",
)
```

Any field entry may be `None` when that layout does not support the semantic. `axis` may describe current linear layouts and leaves room for future Grid/Flow/Wrap/Stack semantics without teaching generic code concrete `kind` names.

Current Row/Column keep their persisted prop names to avoid needless schema churn:

```text
Row:    axis=horizontal, distribution_field=horizontal_distribution,
        cross_alignment_field=vertical_alignment, equal_size_field=equal_widths
Column: axis=vertical, distribution_field=vertical_distribution,
        cross_alignment_field=horizontal_alignment
```

`ui/properties/layout_adapter.py` reads those names through `definition.layout_spec`. It contains no persisted Row/Column field-name routing and no `kind == "row"` / `kind == "column"` dispatch. Specialized Row/Column renderer/Inspector modules may naturally understand their own schema.

A synthetic horizontal `Flow Layout` can therefore use properties such as `flow_policy`, `cross_policy` and `same_extent`; generic editor semantics still work from `LayoutSpec` and require no new core `kind` checks.

## Section semantics

A section is identified by capability `section`; its type-specific mode field is declared separately by `SectionSpec`:

```python
SectionSpec(
    mode_field="display_mode",
    modes=("cards", "stack"),
)
```

The `section` capability does **not** imply a property named `folder_type`. Generic runtime obtains the mode through `definition.section_mode(props)`, which resolves `section_spec.mode_field` and the declared Field. Folder keeps its existing persisted `folder_type` schema through `SectionSpec(mode_field="folder_type", ...)`, but the generic runtime does not know that literal.

A future Card Section with `props.display_mode`, an Accordion Section, Tool Group or Asset Group can therefore participate in generic section routing without changing `ui/runtime.py` or adding a concrete-kind branch. Type-specific rendering behavior still belongs to that Item's renderer.

## Adding and registering Item types

Add the type-specific implementation; do not edit routing core.

For a built-in `video`:

1. add `model/item_definitions/video.py` with its `ItemTypeDefinition`;
2. add its renderer and Inspector modules/classes;
3. include `video_definition()` in the explicit built-in bootstrap tuple;
4. add tests.

Example ordinary Item definition:

```python
from script_toolbox.model.fields import PathField
from script_toolbox.model.item_registry import ItemTypeDefinition

resource = ItemTypeDefinition(
    kind="file",
    title="File",
    fields={"source": PathField(default="")},
    renderer_path=".file_item:render_file",
    inspector_path=".file_item:FilePropertyEditor",
)
```

Example layout definition:

```python
from script_toolbox.model.item_registry import ItemTypeDefinition, LayoutSpec

flow = ItemTypeDefinition(
    kind="flow",
    title="Flow Layout",
    fields={...},
    capabilities=("container", "layout"),
    layout=LayoutSpec(
        axis="horizontal",
        distribution_field="flow_policy",
        cross_alignment_field="cross_policy",
        equal_size_field="same_extent",
    ),
    renderer_path=".flow_layout:render_flow",
    inspector_path=".flow_layout:FlowPropertyEditor",
)
```

Example section definition:

```python
from script_toolbox.model.item_registry import ItemTypeDefinition, SectionSpec

card = ItemTypeDefinition(
    kind="card_section",
    title="Card Section",
    fields={...},
    capabilities=("container", "section"),
    section=SectionSpec(
        mode_field="display_mode",
        modes=("cards", "stack"),
    ),
    renderer_path=".card_section:render_card_section",
    inspector_path=".card_section:CardSectionPropertyEditor",
)
```

No change is required in `bindings.py`, `layouts.py`, runtime dispatch, the property registry, `interface_editor.py`, `item_palette.py`, or document normalization for these types. External/future plugin code can call `register_item_type()` directly and does not need a built-in bootstrap entry.

Built-in `Image` is the production proof of the ordinary Item pattern. The test-only Video, Flow Layout and Card Section definitions prove late runtime registration, custom layout semantics and section semantics with a non-`folder_type` mode field.

## External registration lifecycle

External definitions that may appear in persisted config **must be registered before config normalization/load**. The canonical future plugin startup order is:

```text
initialize model
  -> register built-in Item types
  -> register external/plugin Item types
  -> load + normalize config
  -> initialize UI
```

Late registration is supported for runtime-added types after UI composition: re-entrant UI path resolution and runtime registry synchronization discover the new definition. However, if config loading already encountered an unknown persisted `kind`, the loader is not required to preserve that raw Item for a plugin that might register later. Unknown persisted kinds remain invalid by clean-break policy; there is no placeholder compatibility layer.

## Container, binding and value contracts

Container semantics are definition-owned. Traversal, indexing, reference rewriting, cloning, topology and editor containment use registry capabilities and canonical `walk_items()` behavior rather than a maintained container-kind tuple.

Top-level document sections are expressed by the `section` capability. Layout containers use `layout`; generic editor rules prevent a layout from owning a section without knowing any concrete kind name.

`bindings` are the only persisted/runtime event mechanism. Callback dictionaries and direct script fields are not read or translated. A normal `button` is action-only. Stateful behavior belongs to definitions with `state_toggle`; button chrome is selected through `native_button` rather than concrete kind checks.

Toggle Button and Toggle Icon participate in the generic value API only when `state_source == "internal"`. Script-driven toggles do not persist or acquire a synthetic `props.value` through `store_value()`.

Numeric scalar/vector construction and runtime writes share definition normalizers so size, min/max clamping and component count cannot diverge. Invalid numeric content is rejected instead of being silently replaced with an unrelated fallback. Field values preserve the established runtime contract: scalar values become text, list/tuple values become lists of text values, and single-value fields collapse list input to the first value.

For Icon and Toggle Icon alignment, `content_alignment` is the only type-specific property key. Generic layout alignment belongs to `ui.alignment`.

## Editor architecture

`EditorDocumentController` owns the staged document, identity cache, clone/reference operations and topology. It is Qt-independent.

The base Interface Editor itself uses the registry for palette entries, type titles, container/section semantics and tree structure. `ui/layout_editor_adapter.py` contains reusable capability-driven tree helpers; it does not contain a second list of Folder/Row/Column kinds.

`ui/editor_document_adapter.py` composes controller ownership, command history, search presentation, sharing and view-state preservation around that registry-driven editor. Layout routing no longer requires an adapter-specific kind switch.

The Add Item palette is generated from `ITEM_TYPES.creatable()` metadata each time the editor UI is built. Categories are derived from definition metadata, so a newly registered category appears without editing the Interface Editor.

## UI composition lifecycle

`ui/bootstrap.py` is the UI/runtime composition root. It owns ordered construction of the final `InterfaceEditor` and `ScriptToolbox` classes and installs registry-driven UI/runtime hooks.

`ui/__init__.py` is intentionally declarative. Importing `script_toolbox.ui` initializes the complete UI automatically through one visible composition call:

```python
_RUNTIME = initialize_ui()
```

The resulting `UIComposition` contains the final public classes and the active runtime renderer registry. `from script_toolbox.ui import ScriptToolbox` and `from script_toolbox.ui import InterfaceEditor` therefore keep their public contract.

`initialize_ui()` is idempotent within one loaded module graph: a completed composition is cached and returned on repeated calls. A failed composition is not cached, so a later retry can recover. For development hot reload, bootstrap reuses the active renderer registry when the runtime module object has not changed; reloading `ui.runtime` creates a fresh default registry for the new runtime classes.

## Runtime rendering and synchronization

`RuntimeFolder.build_runtime_widget()` routes through the runtime renderer registry directly. Runtime renderer registration is derived from `ItemTypeDefinition.renderer` after generic UI path resolution; adding a new type does not require editing a renderer switch/table.

Initial registry composition, late Item discovery and manual `register_runtime_renderer()` all converge on one semantic generic decoration function: `_decorate_runtime_renderer_registry(registry)`. That pipeline applies event-binding wrappers and runtime-value wrappers. Their existing marker-based guards make repeated synchronization idempotent; calling the pipeline twice does not produce wrapper-on-wrapper stacking.

Startup-only UI polish whose installer has broader runtime-module responsibilities (for example scroll-frame composition or existing visual polish hooks) remains in bootstrap and is not blindly replayed on every late registration. The shared pipeline contains only generic renderer decorators that are safe to synchronize repeatedly.

All runtime renderers receive the raw universal Item envelope and read `ui` and `props` explicitly. Runtime event filters attach only events declared by the Item definition and dispatch through `bindings`. Runtime value synchronization is capability-driven: ordinary `has_value` Items register a `RuntimeValueBinding`; specialized field refresh uses `field_widget` instead of a concrete kind branch.

Explicit runtime renderer unregister is respected: synchronization does not resurrect a disabled renderer merely because its definition still has a declarative path. A later explicit registration re-enables it and applies the same generic decoration pipeline.

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
      layout_adapter.py
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
- Field schema remains model-only; it does not define Qt widgets.
- Host-specific API access belongs in `hosts/` or host integration modules.
- No JSON file I/O in `ui`.
- Runtime config/settings paths are owned only by `core/user_paths.py`.
- Stable and Development builds share the same canonical user config files.
- Only the current config schema is supported while the project remains in development.
- Persist and operate on Items only through the schema 21 envelope; do not add type-specific root keys or a flat compatibility view.
- Never silently convert an unknown item kind to another kind or preserve it as a placeholder.
- Never use `ui.label` as item identity.
- Persist event behavior only as `bindings`.
- New item types register through `ItemTypeDefinition`; core, palette, events, runtime and Inspector routing derive from that metadata instead of central kind tables.
- Layout semantics belong to `LayoutSpec`; generic layout code must not infer behavior from concrete prop names or Item kinds.
- Section semantics belong to `SectionSpec`; generic section code must not assume a `folder_type` field.
- External definitions that can occur in config register before config load/normalization.
- Structural recursion and editor containment use registry capabilities and canonical traversal.
- Shared network compatibility belongs in `core/http_transport.py`; updater/share must not duplicate PowerShell transport logic.
- Qt binding selection and Qt4/Qt5/Qt6 compatibility belong in `qt_compat.py`; host/UI modules must not create parallel binding logic.
- UI/runtime composition ordering belongs in `ui/bootstrap.py`; `ui/__init__.py` should remain a small public export surface.
- Source remains Python 2.7 compatible until support for the legacy Maya 2015 / Nuke 12 generation is intentionally dropped.
