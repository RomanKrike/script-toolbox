# Architecture

The project is being migrated from the original single-file Maya 2015 tool to a modular package.

## Compatibility target

- Autodesk Maya 2015
- Python 2.7
- PySide 1 / Qt 4
- MEL and Python button scripts
- Existing `maya_script_toolbox.json` configurations

## Dependency direction

```text
ui  -> model -> core/config
 |       |
 |       -> registry
 |
 -> core/executor
 -> style
 -> compat
```

UI code must not mutate raw JSON dictionaries directly. Configuration is normalized by the model layer first.

## Package layout

```text
scripts/script_toolbox/
  __init__.py
  bootstrap.py
  compat.py
  constants.py

  core/
    config.py
    executor.py

  model/
    items.py

  style/
    __init__.py

  ui/
    __init__.py
```

The next extraction steps are:

1. Runtime renderer and runtime widgets.
2. Interface tree model.
3. Property editors per item type.
4. Code editor.
5. Main window and interface editor.
6. Legacy config migrations and regression tests.

## Rules

- No circular imports.
- No Maya UI code in `model`.
- No JSON file I/O in `ui`.
- New item types register through the model/renderer/property-editor registries instead of large `if/elif` chains.
- New source files remain Python 2.7 compatible until Maya 2015 support is intentionally dropped.
