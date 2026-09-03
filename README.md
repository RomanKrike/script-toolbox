# Script Toolbox

Houdini-style configurable script toolbox for Autodesk Maya.

Current compatibility target:

- Maya 2015
- Python 2.7
- PySide 1 / Qt 4
- Python and MEL button scripts

## Refactor status

The original working v15.3 implementation is preserved in:

```text
legacy/maya_script_toolbox_2015_v15_3.py
```

The modular implementation lives under:

```text
scripts/script_toolbox/
```

The runtime has now been extracted and can load existing configs, render nested Folders/Rows, execute buttons and persist parameter values. The Interface Editor is still being extracted, so the gear button in the modular branch currently reports that the editor is not available yet.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the dependency rules and migration plan.

## Maya entry point

With the repository installed as a Maya module:

```python
import script_toolbox
script_toolbox.show()
```

During development:

```python
import script_toolbox
script_toolbox.reload_toolbox()
```

The repository contains `MayaScriptToolbox.mod` for module-based installation.

## Current feature set in the legacy implementation

- Nested Folders
- Collapsible / Simple / Tabs / Radio folder types
- Row layout containers
- Button, String, Integer, Float, Checkbox, Menu, Color, Field, Label and Separator items
- Name / Label separation
- Optional labels
- Python / MEL scripts
- Click / Shift+Click actions
- Embedded code editor
- Import / Export JSON configuration
- Persistent parameter values

## Modular extraction completed

- item/document model
- config I/O
- script execution
- value API
- stylesheet and icons
- code editor
- runtime renderer/widgets
- runtime main window
