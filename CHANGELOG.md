# Changelog

## Unreleased

### Added

- Add a dedicated `Toggle Button` item with independent ON/OFF actions, labels, colors and icon settings.
- Add `Internal` state for persisted boolean toggles and `Script` state for host-driven/query-driven toggles.
- Add a first-run opt-in dialog for anonymous Script Toolbox usage statistics.
- Add Script Toolbox Settings with update-channel and Privacy controls for telemetry consent.
- Add cross-version Qt/PySide compatibility for Maya 2015+, Nuke 12+, and Houdini 19+, including PySide6 / Qt 6 hosts.

### Changed

- Make the regular `Button` item action-only instead of combining action and state behavior in one control type.
- Upgrade config schema to version 19 and migrate existing `button` items with `mode: state` to `toggle_button` with scripted state automatically.
- Keep scripted Toggle Button state external: only Internal toggles persist a boolean `value` in the document.
- Resolve the host Qt binding centrally and reuse an already-loaded binding to avoid intentionally mixing Qt major versions in one DCC process.

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
- Add Field collection API: `get_field_selection()`, `add_to_field()`, `remove_from_field()`, `clear_field()`.

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
