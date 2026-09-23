# Changelog

## 1.0.1 — 2026-09-23

Documentation hotfix for LLM-generated clipboard templates.

### Fixed

- Distinguish clipboard-ready Item JSON from built-in preset-registry source definitions.
- Make a bare "template" request default to an Item/subtree that can be pasted into Import from Clipboard.
- Require strict JSON literals (`true`, `false`, `null`) for clipboard/config output and explicitly reject Python `True` / `False` / `None`.
- Point the stable `llms.txt` entry point at stable `main` documentation/source instead of the moving `dev` branch.

## 1.0.0 — 2026-09-23

Major architecture and multi-DCC release.

### Breaking changes

- Move the configuration contract to schema 21 and the universal Item envelope (`kind`, `id`, `name`, `ui`, `props`, `bindings`, plus `items` for containers).
- Remove the schema-20 compatibility layer and automatic conversion path. Script Toolbox 1.0.0 intentionally accepts the current schema only.
- Treat unknown Item kinds and malformed typed properties as validation errors instead of silently coercing them into unrelated defaults.

Existing 0.10.1/schema-20 configurations are not migrated automatically. Keep a backup of the previous configuration and remain on 0.10.1 if the existing schema-20 document must continue to run unchanged.

### Added

- Add the registry-driven universal Item architecture and declarative field validation.
- Add the Image display Item with contain, cover, and stretch fit modes.
- Add DCC-aware Presets and reusable Item-subtree insertion.
- Add Script Editor autocomplete for Script Toolbox APIs.
- Add shared network transport and configurable System / No proxy / Manual proxy settings with HTTP, HTTPS, and SOCKS5 support.
- Add Windows DPAPI protection for saved proxy credentials and a connection-test UI.
- Add broad Qt/PySide compatibility across Maya 2015+, Nuke 12+, and Houdini 19+.
- Add LLM-oriented documentation through `llms.txt` and the template/preset authoring specification.

### Changed

- Centralize UI composition and runtime renderer registration around Item metadata instead of parallel kind tables.
- Make Settings use category navigation and the same Simple Folder visual language as the runtime.
- Keep Stable and Development as the two updater channels and share one network/proxy transport between updater and encrypted sharing.
- Preserve HScript as a first-class persisted binding language for Houdini, including Toggle ON/OFF actions.

### Fixed

- Fix Maya 2015 full UI imports after the universal Item clean break.
- Fix runtime Field list visibility in Maya 2015.
- Fix trigger-tab ordering, duplicate signatures, state-toggle tabs, and add-tab placement.
- Fix updater PowerShell fallback/proxy behavior and harden shared transport errors.
- Preserve Interface Editor state and keep saved window geometry on screen.

## 0.10.1 — 2026-09-11

Documentation patch release.

### Added

- Add English and Russian GitHub Pages documentation.

## 0.10.0 — 2026-09-11

Multi-DCC, presets, telemetry, and UI architecture release.

### Added

- Add Houdini 19 integration.
- Add dedicated Toggle Button and Toggle Icon items.
- Add multiline Text presentation items.
- Add opt-in PostHog telemetry with privacy-reviewed event schemas and persistent pseudonymous installation IDs.
- Add the Presets palette.
- Add the GitHub Pages documentation site.

### Changed

- Refactor the item architecture around schema 20.
- Improve runtime Folder/Field styling, tab layout, trigger icons, and value synchronization.

## 0.9.1 — 2026-09-08

### Fixed

- Expose the update-channel menu reliably in Runtime.

## 0.9.0 — 2026-09-08

### Added

- Add Stable and Development update channels.

## 0.8.5 — 2026-09-08

Maintenance release for encrypted sharing and updater packaging.

## 0.8.4 — 2026-09-08

Maintenance release for encrypted sharing and runtime stability.

## 0.8.3 — 2026-09-08

### Changed

- Speed up encrypted share transport on legacy Maya/Python 2.

## 0.8.2 — 2026-09-08

Maintenance release for encrypted sharing.

## 0.8.1 — 2026-09-08

### Fixed

- Fix encrypted share-provider failures.

## 0.8.0 — 2026-09-08

### Added

- Add encrypted Script Toolbox configuration/item sharing.

## 0.7.6 — 2026-09-08

Maintenance release for layout/runtime stabilization.

## 0.7.5 — 2026-09-08

Maintenance release for layout/runtime stabilization.

## 0.7.4 — 2026-09-08

Maintenance release for layout/runtime stabilization.

## 0.7.3 — 2026-09-08

Maintenance release for layout/runtime stabilization.

## 0.7.2 — 2026-09-08

Maintenance release for layout/runtime stabilization.

## 0.7.1 — 2026-09-08

Maintenance release for layout/runtime stabilization.

## 0.7.0 — 2026-09-08

### Added

- Add composable Column layouts.
- Add compact trigger-tab editor controls.

## 0.6.0 — 2026-09-08

### Changed

- Unify executable behavior under per-item event bindings.

## 0.5.0 — 2026-09-08

Architecture and reliability release.

### Added

- Add versioned config infrastructure, backup/recovery, cached DocumentIndex lookups, and debounced persistence.
- Add EditorDocumentController, command history, reference remapping, runtime renderer registry, host callbacks, and structured execution diagnostics.
- Add updater transaction v2, icons, universal callbacks, and numeric-controls v2.

## 0.4.4

Configuration and updater safety maintenance release.

### Fixed

- Save toolbox configuration through a same-directory temporary file and atomic replacement.
- Use Windows MoveFileExW replacement for Maya 2015 / Python 2.7 instead of delete-then-rename semantics.
- Warn when an existing configuration cannot be read or parsed instead of silently hiding the failure.
- Keep updater authentication tokens out of the PowerShell command line by passing them through the child environment.
- Back up and restore MayaScriptToolbox.mod together with the Python package when an update fails.
- Remove stale unused imports and editor locals reported by flake8.

### Tests

- Add direct config load/save, corruption, write-failure and replacement-failure tests.
- Add install_release filesystem, rollback, archive-validation and Maya module rollback tests.
- Add flake8 to CI, config coverage, and a Python 2.7 config save/load smoke test.

## 0.4.3

Interface Editor Qt4 polish release.

### Fixed

- Force Parameter Description viewport, host and property-editor backgrounds through QPalette for Maya 2015 Qt4.
- Restore the host-native ComboBox drop-down and arrow instead of replacing the Qt4 subcontrols with QSS.
- Match Create Parameters alternating rows to Existing Parameters.
- Move Label and Separator into Layout and remove the redundant Display palette group.

## 0.4.2

Interface Editor visual consistency patch.

### Fixed

- Restore the Parameter Description background after the 0.4.1 scroll-area change.
- Make ComboBox controls visually read as dropdowns with a distinct right-side button area.
- Expand ComboBox and SpinBox property fields to the same value-column width as text fields.
- Apply the same field-growth policy to Row Layout properties for consistent sizing.

## 0.4.1

Interface Editor regression fix release.

### Fixed

- Make Parameter Description scrollable so Field 2.0 and other large property editors no longer compress or overlap controls.
- Tighten the Field property layout and keep its manual multi-value editor bounded to a compact height.
- Preserve folder/row expansion state while normalizing the Existing Parameters tree.
- Make context-menu Duplicate target the item that opened the menu and keep the duplicated item selected after normalization.

## 0.4.0

Editor and interactive-controls release.

### Added

- Add snapshot-based Undo / Redo to the Interface Editor with Ctrl+Z / Ctrl+Y.
- Add Duplicate, Copy and Paste for parameters and complete Folder/Row subtrees with regenerated IDs and unique names.
- Add import modes for Replace Toolbox, Append to Toolbox and Insert into Selected Folder.
- Add advanced Row layout controls: spacing, equal widths, vertical alignment and per-child Auto / Stretch / Fixed width and alignment.
- Add State mode to Button with Python state queries, ON/OFF scripts, labels and colors.
- Add Python On Change scripts to value controls with `value`, `old_value`, `toolbox` and `host` namespace values.
- Add multi-row Field list display with visible-row control, list multi-selection, Ctrl+C and double-click scene selection.
- Add Field collection API: `get_field_selection()`, `add_to_field()`, `remove_from_field()` and `clear_field()`.

### Changed

- Upgrade config schema to version 16 while preserving normalization of existing configurations.
- Keep Maya and Nuke toolbox configurations independent while sharing the common runtime/editor engine.

## 0.3.8

Separator rendering fix release.

### Fixed

- Render horizontal separators as explicit QSS border strokes instead of relying on a 1 px QFrame background fill.
- Render compact vertical separators with the same explicit border-stroke approach.
- Apply the separator override after the base stylesheet so Maya 2015 Qt4 cannot lose it to earlier QFrame rules.

## 0.3.7

Separator visibility polish release.

### Changed

- Match horizontal and vertical separator color to the Collapsible Folder card border.
- Keep separator spacing unchanged while making separators clearly visible in the dark runtime theme.

## 0.3.6

Section header cleanup release.

### Changed

- Remove the divider line from Simple Section headers, including nested Simple Sections.
- Replace Collapsible Folder QToolButton headers with QPushButton headers for reliable left alignment in Maya 2015.
- Remove the yellow/orange left accent from Collapsible Folder headers.
- Keep the compact text chevron and outlined card hierarchy.

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
- Automatic tested release packaging.

### Compatibility

- Autodesk Maya 2015
- Python 2.7
- PySide 1 / Qt 4