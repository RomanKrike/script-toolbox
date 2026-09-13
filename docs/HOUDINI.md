# Houdini integration

Script Toolbox supports Houdini 19 and newer through the shared host/runtime architecture.

## Compatibility target

Supported Houdini generations:

- Houdini 19–20.x standard Qt 5 builds — PySide2 / Qt 5
- Houdini 20.5 optional Qt 6 builds — PySide6 / Qt 6 when the host selects that binding
- Houdini 21 main builds — PySide6 / Qt 6; separate Qt 5.15.2 builds are also supported through PySide2
- Houdini 22+ — PySide6 / Qt 6; Qt 5 builds were dropped in Houdini 22
- Python and HScript button languages

The host adapter remains Python 2.7 syntax-compatible because Houdini 19.0 was the final Houdini release family with separately published Python 2 builds.

Script Toolbox resolves the binding from the Houdini version, `HOUDINI_QT_PREFERRED_BINDING`, and any binding already loaded by the host. An already-loaded or host-preferred binding wins so Script Toolbox does not intentionally mix Qt major versions in one Houdini process. This also lets Houdini 21 Qt 5 variant builds select PySide2 while the main Houdini 21 build selects PySide6.

## Installation for development

The repository is not copied into the Houdini preferences folder. Point Houdini at the repository `scripts` directory instead.

A simple package file can be created at:

```text
$HOUDINI_USER_PREF_DIR/packages/script_toolbox.json
```

Example:

```json
{
    "env": [
        {
            "SCRIPT_TOOLBOX_ROOT": "C:/path/to/script-toolbox"
        },
        {
            "var": "PYTHONPATH",
            "value": "$SCRIPT_TOOLBOX_ROOT/scripts",
            "method": "prepend"
        }
    ]
}
```

Replace `C:/path/to/script-toolbox` with the local checkout path.

After restarting Houdini, open a Python Shell or shelf tool and run:

```python
import script_toolbox
script_toolbox.show()
```

For development reloads:

```python
import script_toolbox
script_toolbox.reload_toolbox()
```

## Host behavior

Inside Houdini, Script Toolbox uses the `hou` module for:

- Houdini version reporting;
- reading the selected nodes;
- restoring node selection from Field list items;
- object existence checks;
- selection-change callbacks;
- HScript execution;
- resolving `$HOUDINI_USER_PREF_DIR`.

Python button scripts receive both `host` and `hou` in their execution namespace.

The main Script Toolbox window is parented to Houdini's Qt main window. The integration prefers `hou.qt.mainWindow()` and retains `hou.ui.mainQtWindow()` as a compatibility fallback.

## Qt compatibility

The shared UI retains the original Qt 4-style `QtGui` widget namespace. On PySide2 and PySide6 hosts, Script Toolbox mirrors `QtWidgets` into that namespace so the runtime and Interface Editor do not need separate implementations per Houdini generation.

The compatibility layer also supplies the Qt 6 compatibility surface required by the existing editor: the used `QRegExp` API subset, legacy `exec_()` aliases, font-metric width access, and the modern tab-stop API fallback.

## Current scope

The common Script Toolbox runtime and editor run as a normal Qt window across the supported Houdini generations.

A Houdini-native Python Panel descriptor and packaged release installer remain separate follow-up work. They should be validated independently from the cross-version runtime compatibility layer.
