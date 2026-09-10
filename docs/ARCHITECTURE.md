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
ui/main_window -> ui/runtime -> core/values -> model
      |               |
      |               -> style
      |
      -> core/config -> core/config_schema
      -> core/user_paths -> hosts
      -> core/event_bindings -> core/executor
      -> compat -> hosts

core/executor -> hosts
model -> pycompat (pure Python)
hosts/base -> Python stdlib only
hosts/maya_host -> maya.cmds / maya.mel
hosts/nuke_host -> nuke / nukescripts
hosts/houdini_host -> hou
```

The model layer must remain importable without Maya or Qt. Host-specific imports live behind `hosts/`, `compat.py`, and host integration modules.

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

## Runtime rendering

`RuntimeFolder.build_runtime_widget()` routes through the runtime renderer registry directly. The registry is initialized during UI bootstrap and specialized current kinds are registered through its public API.

Runtime event filters attach supported mouse/editing/selection events to rendered widgets and dispatch through `bindings`. Renderer-specific modules do not patch main-window event semantics.

Stateful execution and refresh are owned by the main runtime API. Toggle Button and Toggle Icon renderers only create and register their widgets.

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
- Source remains Python 2.7 compatible until Maya 2015 support is intentionally dropped.
