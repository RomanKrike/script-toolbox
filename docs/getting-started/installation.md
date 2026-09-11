# Installation

Script Toolbox is distributed as a versioned ZIP archive in GitHub Releases. The archive contains the shared `scripts/script_toolbox` package plus host-specific integration files.

## Download a stable release

1. Open the repository **Releases** page.
2. Download `script-toolbox-<version>.zip` from the latest stable release.
3. Extract the archive to a permanent location. Do not run the plugin directly from inside the ZIP file.

Stable releases are produced from `main`. Development builds are produced separately from `dev` and are intended for testing upcoming changes.

## Maya

The release contains `MayaScriptToolbox.mod` for Maya module-based installation.

Make the directory containing `MayaScriptToolbox.mod` visible to Maya through your normal module path setup. Once the module is available, open Script Toolbox from Python:

```python
import script_toolbox
script_toolbox.show()
```

For development or after editing plugin code in place:

```python
import script_toolbox
script_toolbox.reload_toolbox()
```

## Nuke

The release contains a `nuke` directory and `nuke/menu.py.example`. Configure Nuke so that the shared `scripts` directory is on Python's module path, then use:

```python
import script_toolbox
script_toolbox.show()
```

To register the application menu:

```python
import script_toolbox
script_toolbox.register_nuke_menu()
```

To register the dockable panel:

```python
import script_toolbox
script_toolbox.register_nuke_panel()
```

See the [Nuke integration notes](../NUKE.md) for the repository-level setup details.

## Houdini

Point Houdini at the release `scripts` directory through `PYTHONPATH`, then run:

```python
import script_toolbox
script_toolbox.show()
```

For development:

```python
import script_toolbox
script_toolbox.reload_toolbox()
```

See the [Houdini integration notes](../HOUDINI.md) and the included `houdini/script_toolbox.json.example` package file.

## Update channels

Script Toolbox supports three update channels:

- **Stable** — published releases from `main`;
- **Latest** — newest appropriate published version;
- **Development** — test builds from `dev`.

Use Stable for normal production work. Use Development only when you intentionally want to test the next release.

## User configuration

Your toolbox configuration and settings are stored outside the installed package in the host user configuration area. Stable and Development builds use the same host user-config location, so changing update channels does not create a separate toolbox configuration.
