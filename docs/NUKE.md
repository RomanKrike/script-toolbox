# Nuke integration

Script Toolbox supports Nuke through the same core model, Interface Editor, runtime widgets, updater, and JSON schema used by Maya and Houdini.

## Compatibility target

Supported Nuke generations:

- Nuke 12–15 — PySide2 / Qt 5
- Nuke 16+ — PySide6 / Qt 6
- Python button scripts on every supported generation

The runtime detects the Nuke version and resolves the matching Qt binding. If the host already loaded a PySide generation, Script Toolbox reuses that binding rather than loading a different Qt major into the same process.

MEL remains available only when the active host is Maya.

## Automatic installation

Use **Settings → DCC Integrations → Foundry Nuke** from standalone Script Toolbox.

For each detected Nuke version, **Install** manages a marked block inside:

```text
~/.nuke/menu.py
```

The block adds the Script Toolbox `scripts` directory to Python's search path and applies the settings for the Nuke version that is currently running. Existing `menu.py` content is preserved and receives a one-time `.script_toolbox.bak` backup before Script Toolbox edits it.

Options:

- **Add to Main Menu**
- **Register Dock Panel**
- **Open on startup**

Nuke versions share the same `~/.nuke/menu.py` bootstrap, while their options are stored independently. Uninstalling one configured version does not remove the shared bootstrap if another Nuke version still uses it.

**Repair** recreates a missing managed startup block. **Update** rewrites a stale Script Toolbox path.

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
