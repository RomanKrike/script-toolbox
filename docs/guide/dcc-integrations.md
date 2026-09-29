# DCC integrations

Script Toolbox can detect installed DCC applications and manage host integration from **Settings → DCC Integrations**.

## Current support

| DCC | Detection | Managed integration |
| --- | --- | --- |
| Autodesk Maya | Yes | Yes |
| SideFX Houdini | Yes | No |
| Foundry Nuke | Yes | No |
| Blender | Yes | No |
| Autodesk 3ds Max | Yes | No |

Only Maya is marked **Supported** in the first implementation. The other adapters expose detection and capability information without claiming that automatic integration is available.

## Maya integration

Each detected Maya profile target is configured independently. A target is a Maya version plus its user-profile location, so the same Maya version can be integrated into both the default profile and one or more studio-launcher profiles.

The page supports:

- **Install**
- **Update**
- **Repair**
- **Uninstall**
- **Add to Shelf**
- **Add to Main Menu**
- **Open ScriptToolbox on Maya startup**
- **Install to all detected Maya profiles**
- **Add profile path...** for custom Maya preference roots

The loader is intentionally minimal. Script Toolbox is not copied into each Maya preferences folder; the generated Maya module points to the installed Script Toolbox distribution.

Per-profile integration state is stored outside the normal host-specific toolbox configuration. Maya 2025 Default and Maya 2025 Studio, for example, can keep different Shelf, Main Menu, and startup choices without colliding.

## Custom Maya profile locations

Studio launchers commonly override `MAYA_APP_DIR`, which moves Maya's prefs, scripts, shelves, and user module directory away from the standard `Documents/maya` location.

Open the **Autodesk Maya** section and expand **Profile locations**. The Default Maya profile root is listed automatically. Use **Add profile path...** to add another root, for example:

```text
C:\\studio\\preferences\\maya\\username
```

Script Toolbox scans that root for version directories such as `2024`, `2025`, and `2026`. You can also select a specific version directory directly.

Each discovered target is shown separately, for example:

```text
2025 - Default  |  Installed
2025 - Studio   |  Not installed
```

The custom root name is user-defined when the path is added.

At Maya runtime, Script Toolbox compares Maya's actual `userAppDir` / user prefs location with the saved custom roots and loads the settings for the matching profile. This lets a studio-launched Maya use different integration settings from a normal Maya of the same version.

A custom profile path cannot be removed while Script Toolbox integration is still installed in one of its discovered profiles. Uninstall those targets first, then remove the search path.

## Files managed for Maya

For each Maya profile target, Script Toolbox may manage:

- `<maya user config>/modules/ScriptToolboxIntegration.mod`
- a marked Script Toolbox block inside `<maya user config>/scripts/userSetup.py`
- `<maya user config>/prefs/shelves/shelf_ScriptToolbox.mel`

Maya's documented default module search paths include the per-version user `modules` directory, so the version-scoped module file can be discovered without editing `MAYA_MODULE_PATH`.

## Safety rules

Installation is idempotent: running Install or Apply Changes repeatedly does not duplicate the startup block or Shelf entry.

Existing `userSetup.py` content is preserved. Script Toolbox edits only the block between its own markers and creates a one-time `.script_toolbox.bak` backup before changing an existing startup file.

A pre-existing `shelf_ScriptToolbox.mel` that is not marked as Script Toolbox-managed is treated as user-owned and is not overwritten.

Uninstall removes only Script Toolbox-managed artifacts for the selected Maya profile target. Other versions, other profiles of the same version, and unrelated user startup code are preserved.

## Status model

The integration page derives status from both stored configuration and managed files:

- **Not installed** — no configured integration artifacts are present.
- **Installed** — the loader and selected components match the stored configuration.
- **Partially installed** — a selected component is missing or does not match.
- **Broken** — a required managed loader is missing or cannot be verified.
- **Update required** — the loader points at an older Script Toolbox version or location.
- **Unsupported** — automatic integration has not been implemented for that DCC.

Use **Repair** for missing or damaged managed artifacts. Use **Update** when the loader is stale.

## Manual validation scenarios

Use these checks when validating a packaged build on a workstation with Maya installed.

### A. Fresh Maya install

Open standalone Script Toolbox → Settings → DCC Integrations → Scan DCCs. Confirm the installed Maya version is detected and reports **Not installed**.

### B. Default install

Enable Shelf and Main Menu, leave startup auto-open disabled, then Install. Restart Maya. Confirm the ScriptToolbox Shelf and top-level ScriptToolbox menu appear and the toolbox does not open automatically.

### C. Startup auto-open

Enable **Open ScriptToolbox on Maya startup**, apply changes, restart Maya, and confirm the toolbox opens once.

### D. Independent versions and profiles

Configure two installed Maya versions differently, or configure Default and Studio profiles of the same Maya version differently. Restart each target through its normal launcher and verify the matching profile configuration is used.

### E. Idempotency

Run Install or Apply Changes repeatedly. Confirm `userSetup.py` contains one Script Toolbox marker block and the Shelf contains one ScriptToolbox button.

### F. Repair and update

Delete a managed Shelf file and confirm status becomes **Partially installed**; Repair should recreate it. Change or replace the managed module content and confirm **Update required**; Update should return status to **Installed**.

### G. Scoped uninstall

Add unrelated code to `userSetup.py`, uninstall Script Toolbox integration for one Maya profile, and confirm that unrelated code, other Maya versions, and another profile of the same Maya version remain intact.

### H. Custom studio profile

Add a custom Maya profile root, confirm its version folders appear as separate targets, install Script Toolbox into one of them, and launch Maya through the studio launcher. Confirm the Script Toolbox module, Shelf, and Main Menu are available from the studio profile without requiring the default Maya profile.

## Remaining work

Automatic installers are still to be implemented for Houdini, Nuke, Blender, and 3ds Max. Their adapters currently provide discovery/capability scaffolding only.
