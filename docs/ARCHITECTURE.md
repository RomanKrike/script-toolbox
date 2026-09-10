# Architecture

Script Toolbox is a modular multi-DCC toolbox targeting Maya and Nuke from a shared model/core.

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
- Host-specific `nuke_script_toolbox.json` configuration

Historical Script Toolbox config schemas are intentionally **not** a compatibility target while the plugin is still under active development.

## Dependency direction

```text
ui/main_window -> ui/runtime -> core/values -> model
      |               |
      |               -> style
      |
      -> core/config -> config schema validation
      -> core/executor
      -> compat -> hosts

core/config -> hosts
core/executor -> hosts
model -> pycompat (pure Python)
hosts/base -> Python stdlib only
hosts/maya_host -> maya.cmds / maya.mel
hosts/nuke_host -> nuke / nukescripts
```

The model layer must remain importable without Maya. Maya/PySide imports live behind `compat.py` and UI/core integration modules.

## Current config schema

Schema **20** is the single supported configuration contract.

```text
JSON read
  -> require schema version 20
  -> normalize current-schema values/defaults
  -> runtime document
```

A non-empty document without a version, an older schema, and a newer schema are all rejected. The config layer must never infer, migrate, or down-convert historical payloads. An empty mapping is used internally only to construct a brand-new current-schema document.

Breaking schema changes during development may advance `CONFIG_VERSION`, but the repository must keep only the current schema contract and current-schema tests unless backward compatibility is explicitly reintroduced as a product requirement.

## Item model contracts

Container semantics are model-owned. `folder`, `row`, and `column` are the canonical container kinds; all document traversal, indexing, reference rewriting, cloning, topology and cache logic must use the shared container predicate and canonical `walk_items()` implementation. Correctness must not depend on importing `ui` or monkey-patching another model module during bootstrap.

Item construction is owned by the model factory registry. `button`, `toggle_button`, `icon`, `toggle_icon`, value controls, `row`, `column`, and `folder` are native item kinds. Unknown kinds are rejected instead of being silently converted to another item type.

Identity has one explicit contract:

- `id` is the canonical stable internal identifier and should be preferred for durable references.
- `name` is the supported symbolic identifier for scripts and human-readable API usage.
- `label` is presentation text only and never participates in lookup.

`bindings` are the only persisted/runtime event mechanism. Historical callback dictionaries and direct script fields are not read or translated. A normal `button` is action-only. Stateful behavior belongs to the dedicated `toggle_button` and `toggle_icon` kinds and uses the native `state_toggle` binding handler.

For Icon and Toggle Icon alignment, `content_alignment` is the only schema key. `alignment` is not an alias.

Numeric scalar/vector construction and runtime writes share the same normalizer so size, min/max clamping, component count and fallback behavior cannot diverge.

## Runtime rendering

`RuntimeFolder.build_runtime_widget()` routes through the runtime renderer registry directly. The registry is initialized normally during UI bootstrap; it does not replace `RuntimeFolder.build_runtime_widget()` or store a legacy implementation for fallback.

New renderable item kinds should be added through the item factory, renderer and property-editor registries rather than through compatibility wrappers or expanding cross-module `if/elif` dispatch chains.

## Current package layout

```text
scripts/script_toolbox/
  __init__.py
  bootstrap.py
  compat.py
  pycompat.py
  constants.py
  nuke_integration.py

  hosts/
    __init__.py
    base.py
    maya_host.py
    nuke_host.py

  core/
    config.py
    editor_document.py
    event_bindings.py
    executor.py
    references.py
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
    runtime.py
    runtime_renderers.py
    interface_tree.py
    interface_editor.py
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
- Only the current config schema is supported while the project remains in development.
- Never silently convert an unknown item kind to another kind.
- Never use `label` as item identity.
- Persist event behavior only as `bindings`.
- Persist icon alignment only as `content_alignment`.
- New item types register through model/renderer/property-editor registries.
- Source remains Python 2.7 compatible until Maya 2015 support is intentionally dropped.
