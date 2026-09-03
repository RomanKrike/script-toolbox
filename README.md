# Script Toolbox

Houdini-style configurable script toolbox for Autodesk Maya.

Current compatibility target:

- Maya 2015
- Python 2.7
- PySide 1 / Qt 4
- Python and MEL button scripts

## Repository status

The original working implementation is preserved in:

```text
legacy/maya_script_toolbox_2015_v15_3.py
```

The project is now being migrated from the single-file prototype to a modular package under:

```text
scripts/script_toolbox/
```

The modular branch is intentionally work in progress. The model, config and script execution boundaries are extracted first; runtime UI and the interface editor are moved afterwards.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the dependency rules and migration plan.

## Planned package entry point

After the runtime UI extraction is complete:

```python
import script_toolbox
script_toolbox.show()
```

For Maya module installation, the repository contains:

```text
MayaScriptToolbox.mod
```

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
