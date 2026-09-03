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

The runtime and the first modular Interface Editor are now extracted. Existing configs can be loaded, nested Folders/Rows are rendered, buttons execute, parameter values persist, and interface changes remain staged until Apply/Accept.

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
- advanced reusable script editor with Undo/Redo, Find, comment/uncomment, indent/unindent, Run and captured output
- runtime renderer/widgets
- runtime main window

## Updates

Script Toolbox checks GitHub Releases in a background thread when the window opens.

If a newer release exists, an **UPDATE x.y.z** button appears in the top bar. The updater downloads the release archive, replaces only the installed plugin package, preserves the Maya user configuration, and then asks for a Maya restart.

Releases are created from tags matching the plugin version:

```text
v0.2.0
```

The repository is currently private. For private-repository update checks Maya needs a GitHub token in the environment:

```text
SCRIPT_TOOLBOX_GITHUB_TOKEN
```

No token is stored in the toolbox config. If the repository becomes public, no token is required.

