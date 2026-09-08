# Architecture

Script Toolbox is a modular multi-DCC toolbox. The first implementation was migrated from the original single-file Maya 2015 tool; the same core now also targets Nuke.

## Compatibility targets

### Maya
- Autodesk Maya 2015
- Python 2.7
- PySide 1 / Qt 4
- Python and MEL button scripts
- Existing `maya_script_toolbox.json` configurations

### Nuke
- Nuke 12
- Python 2.7
- PySide2 / Qt 5
- Python button scripts
- Host-specific `nuke_script_toolbox.json` configuration

## Dependency direction

```text
ui/main_window -> ui/runtime -> core/values -> model
      |               |
      |               -> style
      |
      -> core/config -> core/migrations
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
    executor.py
    values.py
    updater.py
    migrations/
      __init__.py
      v15_to_v16.py

  model/
    items.py

  style/
    __init__.py
    stylesheet.py
    icons.py

  ui/
    __init__.py
    code_editor.py
    script_editor.py
    runtime.py
    interface_tree.py
    interface_editor.py
    update_ui.py
    main_window.py

    properties/
      base.py
      registry.py
      folder.py
      row.py
      basic.py
      field.py
      button.py
```

## Config migration contract

Configuration migration is separate from current-schema normalization:

```text
JSON read
  -> detect schema version
  -> run explicit version-by-version migrations
  -> normalize current-schema values/defaults
  -> runtime document
```

Schema 15 is the compatibility baseline used by the first modular release. Versionless legacy documents are treated as schema 15. The current schema is 16, so the registered chain is currently `15 -> 16`.

A document whose schema is newer than the running Script Toolbox is rejected instead of being normalized to an older shape. This prevents an older plugin from silently down-converting and later overwriting a newer configuration.

Future schema changes must add a new migration module and register exactly one forward step, for example `v16_to_v17.py`. Model normalization should continue to provide current defaults; migrations should contain only version-specific structural or semantic changes.

## Extracted now

- normalized item/document model
- explicit config migration pipeline (schema 15 -> 16)
- legacy Toggle -> Checkbox normalization
- config I/O
- script executor
- runtime value API
- stylesheet
- programmatic icons
- code editor and syntax highlighter
- reusable advanced script editor toolbar/output widget
- runtime widgets and nested Folder renderer
- modular runtime main window
- modular Interface Editor orchestration
- property-editor registry
- GitHub Releases updater with background check/install workers
- DCC host abstraction
- Maya host adapter
- Nuke host adapter
- Nuke menu and dock-panel registration

The modular runtime can now open and execute existing toolbox configurations.

## Still to finish

1. Add automated host-integration harnesses around Maya/Nuke APIs.
2. Harden updater rollback/install behavior on Windows permission failures.
3. Expand editor/tree regression coverage.
4. Add optional per-item host visibility and host-specific script variants.
5. Remove the legacy implementation only after verified feature parity.

## Rules

- No circular imports.
- No DCC UI/API code in `model`.
- Host-specific API access belongs in `hosts/` or host integration modules.
- No JSON file I/O in `ui`.
- Every config schema bump requires an explicit forward migration step.
- Never silently down-convert a config whose schema is newer than the running plugin.
- New item types should register through model/renderer/property-editor registries instead of growing large cross-module `if/elif` chains.
- Source remains Python 2.7 compatible until Maya 2015 support is intentionally dropped.
- `legacy/maya_script_toolbox_2015_v15_3.py` remains the behavioral reference until modular feature parity.
