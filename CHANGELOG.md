# Changelog

## 0.3.5

Runtime spacing polish release.

### Changed

- Remove the divider line between an open Collapsible Folder header and its content.
- Force Collapsible Folder titles to align to the left in Maya and Nuke.
- Replace native separator frames with dedicated separator widgets.
- Give horizontal separators equal top and bottom spacing.
- Give compact vertical separators equal left and right spacing.

## 0.3.4

Collapsible card hierarchy release.

### Changed

- Draw every Collapsible Folder as one outlined card, including top-level sections.
- Visually attach the Collapsible header to the card outline with a subtle divider.
- Replace Maya's oversized native disclosure arrow with compact text chevrons.
- Keep nested Collapsible cards quieter than top-level sections while preserving clear ownership.
- Increase content padding inside Collapsible cards so controls do not sit directly on the outline.

## 0.3.3

Runtime grouping polish release.

### Changed

- Tighten Collapsible Section headers so the native chevron and header bar are less visually heavy.
- Draw nested Folders as subtle bordered group cards so subsection ownership is immediately visible.
- Give nested Collapsible and Simple section headers a quieter visual treatment than top-level sections.
- Make Runtime Folder content backgrounds transparent so nested group cards read as real containers.

## 0.3.2

Interface polish release.

### Changed

- Redesign Collapsible Folder headers as full-width clickable section bars with native chevrons.
- Make the complete Collapsible header clickable instead of only the arrow.
- Improve folder content indentation and visual hierarchy.
- Rename Folder types to clearer Collapsible Section / Simple Section labels.
- Group Interface Editor parameters into Layout, Inputs, Actions and Display.
- Add a parameter filter field to the Interface Editor.
- Improve Folder and Row hierarchy styling in the Existing Parameters tree.

## 0.3.1

Python 2 script-source compatibility release.

### Fixed

- Normalize Unicode Python source before compile so encoding cookies do not fail in Maya/Nuke Python 2.
- Apply the same source preparation in Button execution and the embedded Script Editor.
- Add regression coverage for first-line and second-line encoding cookies.

## 0.3.0

First multi-DCC release.

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
