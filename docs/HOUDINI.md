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

## Automatic installation

Use **Settings → DCC Integrations → SideFX Houdini** from the standalone Script Toolbox build.

For a detected Houdini version, **Install** creates:

```text
$HOUDINI_USER_PREF_DIR/packages/script_toolbox.json
$HOUDINI_USER_PREF_DIR/script_toolbox_integration/
```

The package points at the installed Script Toolbox distribution; the repository is not copied into the Houdini preferences directory. The managed plugin directory provides startup hooks and the optional Script Toolbox Shelf.

Options:

- **Add Houdini Shelf**
- **Open on startup**

The Shelf definition is loaded through Houdini's normal `toolbar` resource path. Script Toolbox shows/hides the tab with Houdini's `shelfdock add/remove` command and does **not** call `hou.ShelfSet.setShelves()`. This avoids modifying factory/user shelf-set definition files and prevents the “Could not save some of the shelf elements to their definition files” warning.

**Repair** recreates missing managed files. **Update** refreshes stale package paths/version metadata. **Uninstall** removes only Script Toolbox-managed package/plugin files and does not edit `houdini.env`.

Restart Houdini after installing from standalone so Houdini processes the package during startup. When Script Toolbox runs inside the matching Houdini process it also attempts a live UI sync.

### Custom profile locations

Expand **Profile locations** in the Houdini section to add studio or launcher-specific preferences.

You can select either:

```text
D:\\studio\\houdini-prefs
    houdini20.5
    houdini21.0
```

or a concrete preferences directory such as:

```text
D:\\studio\\show\\prefs
```

If the selected root contains `houdiniX.Y` children, Script Toolbox maps installed Houdini builds to those folders by major/minor version. Otherwise the selected directory is treated as the direct custom `HOUDINI_USER_PREF_DIR`.

Default and custom targets of the same Houdini version keep independent integration settings.

## Manual development setup

The managed installer uses the same Houdini package mechanism as a manual development setup. The example package remains available at:

```text
houdini/script_toolbox.json.example
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

The managed package installer is available from Settings → DCC Integrations. A Houdini-native Python Panel descriptor remains separate follow-up work; the current integration exposes Script Toolbox through its managed Shelf and normal floating window.
