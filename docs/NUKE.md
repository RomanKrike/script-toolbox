# Nuke integration

Script Toolbox supports Nuke through the same core model, Interface Editor, runtime widgets, updater, and JSON schema used by Maya and Houdini.

## Compatibility target

Supported Nuke generations:

- Nuke 12–15 — PySide2 / Qt 5
- Nuke 16+ — PySide6 / Qt 6
- Python button scripts on every supported generation

The runtime detects the Nuke version and resolves the matching Qt binding. If the host already loaded a PySide generation, Script Toolbox reuses that binding rather than loading a different Qt major into the same process.

MEL remains available only when the active host is Maya.

## Install

Extract a Script Toolbox release to a stable location, for example:

```text
C:\Tools\script-toolbox-0.3.0
```

Add the release `scripts` directory to Nuke's Python path from `~/.nuke/menu.py`:

```python
import os
import sys

ROOT = r"C:\Tools\script-toolbox-0.3.0"
SCRIPTS = os.path.join(ROOT, "scripts")

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import script_toolbox
script_toolbox.register_nuke_menu()
```

A ready-to-edit example is included in releases as:

```text
nuke/menu.py.example
```

## Usage

Floating window:

```python
import script_toolbox
script_toolbox.show()
```

Register the dockable Nuke pane:

```python
import script_toolbox
script_toolbox.register_nuke_panel()
```

The Nuke application menu also exposes these actions after `register_nuke_menu()`.

## Script namespace

Python buttons in Nuke receive:

```python
nuke
nukescripts
host
toolbox
```

Example:

```python
for node in nuke.selectedNodes():
    if "disable" in node.knobs():
        node["disable"].setValue(True)
```

In Maya, the equivalent namespace continues to expose:

```python
cmds
mel
host
toolbox
```

## Selection Fields

A Field with `Source = Selection` follows the active DCC selection.

In Nuke the stored values are node names or full node names. Double-click can reselect the stored nodes.

## Config files

Maya keeps the existing config location and filename:

```text
<maya user prefs>/maya_script_toolbox.json
```

Nuke uses:

```text
~/.nuke/nuke_script_toolbox.json
```

Both use the same JSON schema, so configs can be exported/imported between hosts. Host-specific scripts still need to use the correct DCC API.

## Qt compatibility

The shared UI was originally written against the Qt 4 / PySide 1 layout where widgets live under `QtGui`. Script Toolbox mirrors `QtWidgets` onto the compatibility `QtGui` namespace for Qt 5 and Qt 6 hosts, so Nuke 12–15 and Nuke 16+ use the same widget implementation.

The compatibility layer also covers the Qt 6 removals used by the editor, including the `QRegExp` subset, legacy `exec_()` calls and font-metric width access.

## Updates

GitHub Releases are shared by all supported hosts. On Windows, old Python 2.7 HTTPS stacks can fall back to the hidden PowerShell/.NET TLS transport.

The current package is pure Python/PySide, so successful updates are hot-reloaded when possible. Restarting the host remains the fallback when reload fails.
