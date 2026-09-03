# Architecture

Script Toolbox is being migrated from the original single-file Maya 2015 tool to a modular package.

## Compatibility target

- Autodesk Maya 2015
- Python 2.7
- PySide 1 / Qt 4
- MEL and Python button scripts
- Existing `maya_script_toolbox.json` configurations

## Dependency direction

```text
ui/main_window -> ui/runtime -> core/values -> model
      |               |
      |               -> style
      |
      -> core/config
      -> core/executor
      -> compat (Maya/PySide only)

model -> pycompat (pure Python)
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

  core/
    config.py
    executor.py
    values.py
    updater.py

  model/
    items.py

  style/
    __init__.py
    stylesheet.py
    icons.py

  ui/
    __init__.py
    code_editor.py
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

## Extracted now

- normalized item/document model
- legacy Toggle -> Checkbox migration
- config I/O
- script executor
- runtime value API
- stylesheet
- programmatic icons
- code editor and syntax highlighter
- runtime widgets and nested Folder renderer
- modular runtime main window
- modular Interface Editor orchestration
- property-editor registry
- GitHub Releases updater with background check/install workers

The modular runtime can now open and execute existing toolbox configurations.

## Still to finish

1. Restore the advanced code-editor toolbar actions from the legacy editor.
2. Add explicit version-by-version legacy config migrations.
3. Add Maya/PySide1 integration testing on a real Maya 2015 environment.
4. Harden updater rollback/install behavior on Windows permission failures.
5. Expand editor/tree regression coverage.
6. Remove the legacy implementation only after verified feature parity.

## Rules

- No circular imports.
- No Maya UI code in `model`.
- No JSON file I/O in `ui`.
- New item types should register through model/renderer/property-editor registries instead of growing large cross-module `if/elif` chains.
- Source remains Python 2.7 compatible until Maya 2015 support is intentionally dropped.
- `legacy/maya_script_toolbox_2015_v15_3.py` remains the behavioral reference until modular feature parity.
