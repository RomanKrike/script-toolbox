# Changelog

## 0.3.0-dev

Multi-DCC development branch.

### Added

- DCC host abstraction with Maya and Nuke adapters.
- Nuke 12 / Python 2.7 / PySide2 runtime support.
- Nuke selection-aware Fields.
- Nuke Python button namespace with `nuke`, `nukescripts`, `host`, and `toolbox`.
- Nuke application-menu registration and dock-panel registration.
- Host-specific config locations while preserving the existing Maya config path.
- Nuke startup example included in release packages.

### Fixed

- Avoid the Python 2 implicit-relative-import collision between the Nuke host adapter and Nuke's built-in `nuke` module by using `nuke_host.py` and an explicit validated Nuke API resolver.

### Changed

- Core config and script execution no longer depend directly on Maya.
- Qt compatibility layer now supports PySide1/Qt4 in Maya and PySide2/Qt5 in Nuke.
- Interface Editor and runtime labels identify the active DCC host.

## 0.2.5

Hot-update verification release.

### Changed

- Version bump used to verify the complete in-place updater flow from 0.2.4 to 0.2.5 without restarting Maya.
- No functional config changes; existing Toolbox settings remain compatible.

## 0.2.4

Hot-reload updater release.

### Added

- Reload Script Toolbox in-place after a successful Python package update.
- Close the old Toolbox UI, unload all `script_toolbox.*` child modules, reload the package root in place, and reopen the Toolbox from the newly installed files.
- Preserve existing external `import script_toolbox` references while refreshing `script_toolbox.__version__`.

### Changed

- Successful updates no longer require a Maya restart under the current pure-Python/PySide architecture.
- If hot reload fails, the installed update is kept and the user is asked to restart Maya as a fallback.

## 0.2.3

Updater UX fix for Windows.

### Fixed

- Run the PowerShell/.NET TLS fallback without opening a visible console window.
- Keep update checks and downloads fully background-only from the user's perspective.

## 0.2.2

Updater compatibility fix for Maya 2015 on Windows.

### Fixed

- Fall back to Windows PowerShell/.NET TLS 1.2 when Maya 2015 Python 2.7 `urllib` cannot reach GitHub.
- Prefer public GitHub release `browser_download_url` assets.
- Show update-check failures in the Toolbox status bar instead of failing silently.
- Add a manual Check for Updates button.

## 0.2.1

Updater verification release.

### Changed

- Display the installed Script Toolbox version directly in the main window title and top bar.
- Used as the first end-to-end update test from 0.2.0 to 0.2.1.

## 0.2.0

First modular release of Script Toolbox for Autodesk Maya 2015.

### Added

- Modular package architecture for Python 2.7 / PySide 1.
- Runtime renderer for nested Folder, Row, Tabs and Radio layouts.
- Modular Interface Editor with staged Apply / Accept / Cancel.
- Property-editor registry.
- Reusable script editor with Python/MEL execution and captured output.
- JSON import/export.
- GitHub Releases updater with background checks, package backup/rollback and SHA-256 verification.
- GitHub Actions unit tests, coverage checks, Python 2.7 syntax validation and release-package validation.
- Automatic tested release packaging.

### Compatibility

- Autodesk Maya 2015
- Python 2.7
- PySide 1 / Qt 4
