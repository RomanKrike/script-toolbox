# Script Toolbox

Houdini-style configurable script toolbox for Maya and Nuke.

Current compatibility targets:

- Maya 2015 — Python 2.7, PySide 1 / Qt 4, Python + MEL
- Nuke 12 — Python 2.7, PySide2 / Qt 5, Python

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

The repository contains `MayaScriptToolbox.mod` for Maya module-based installation.

## Nuke entry point

Inside Nuke:

```python
import script_toolbox
script_toolbox.show()
```

Register the Nuke application menu:

```python
import script_toolbox
script_toolbox.register_nuke_menu()
```

Register the dockable Nuke panel:

```python
import script_toolbox
script_toolbox.register_nuke_panel()
```

See [docs/NUKE.md](docs/NUKE.md) and `nuke/menu.py.example` for installation.

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

If a newer release exists, an **UPDATE x.y.z** button appears in the top bar. The updater downloads and verifies the release archive, replaces only the installed plugin package, preserves the Maya user configuration, then hot-reloads Script Toolbox and reopens it from the new files. A Maya restart is only the fallback if hot reload fails.

On Maya 2015 for Windows, if Python 2.7 cannot negotiate GitHub HTTPS correctly, the updater transparently uses a hidden PowerShell/.NET TLS 1.2 fallback.

Releases are created from tags matching the plugin version:

```text
v0.2.0
```

The repository is public, so normal update checks do not require credentials. `SCRIPT_TOOLBOX_GITHUB_TOKEN` remains supported for private forks and is never stored in the toolbox configuration.


## Continuous integration

Every push and pull request runs GitHub Actions checks:

- unit tests on Python 3.8 and Python 3.11;
- coverage for the Maya-independent model/core code, with a minimum threshold;
- Python 2.7 compile check in a Docker image to catch Maya 2015 syntax incompatibilities;
- release-package contract tests;
- upload of the Python 3.11 coverage XML report as a workflow artifact.

The tests cover the item model, nested Folder/Row normalization, legacy Toggle migration, value normalization, code-editor text transforms, updater version handling, release asset selection, ZIP path traversal protection, SHA-256 verification, and release package construction.

## Automatic releases

Releases are gated by the **Python checks** workflow.

When a stable `PLUGIN_VERSION` such as:

```python
PLUGIN_VERSION = "0.2.0"
```

reaches `main` and all checks pass, GitHub Actions automatically:

1. reads the plugin version;
2. builds `script-toolbox-<version>.zip`;
3. generates a SHA-256 checksum;
4. validates the archive layout;
5. creates the matching `v<version>` tag when needed;
6. creates a GitHub Release with generated release notes;
7. uploads the ZIP and checksum as release assets.

Development versions such as `0.2.0-dev` are intentionally not released.

Subsequent pushes with the same stable version do not create duplicate releases.
