# Houdini 19 integration

Script Toolbox supports Houdini 19.0 as a host target.

## Compatibility target

The initial Houdini target is:

- Houdini 19.0
- Python 3.7 default builds
- PySide2 / Qt 5
- Python and HScript button languages

The host adapter is also kept Python 2.7 syntax-compatible because Houdini 19.0 was the final Houdini release family with separately published Python 2 builds.

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

## Current scope

This is the first Houdini integration slice. It covers the common Script Toolbox runtime and editor as a normal Qt window.

A Houdini-native Python Panel descriptor and packaged release installer are intentionally separate follow-up work. They should be added after the Houdini 19 runtime is validated inside a real Houdini session.
