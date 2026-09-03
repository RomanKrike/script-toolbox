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
    main_window.py
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

The modular runtime can now open and execute existing toolbox configurations.

## Still to extract

1. Interface tree / drag-drop editor.
2. Property editors per item type.
3. Interface Editor orchestration.
4. Import/export editor actions.
5. Legacy config migrations as explicit versioned steps.
6. Full regression coverage.
7. Remove the legacy implementation after feature parity.

## Rules

- No circular imports.
- No Maya UI code in `model`.
- No JSON file I/O in `ui`.
- New item types should register through model/renderer/property-editor registries instead of growing large cross-module `if/elif` chains.
- Source remains Python 2.7 compatible until Maya 2015 support is intentionally dropped.
- `legacy/maya_script_toolbox_2015_v15_3.py` remains the behavioral reference until modular feature parity.
