# Changelog

## Unreleased

### Added

- Add a dedicated `Toggle Button` item with independent ON/OFF actions, labels, colors and icon settings.
- Add `Internal` state for persisted boolean toggles and `Script` state for host-driven/query-driven toggles.

### Changed

- Make the regular `Button` item action-only instead of combining action and state behavior in one control type.
- Upgrade config schema to version 19 and migrate existing `button` items with `mode: state` to `toggle_button` with scripted state automatically.
- Keep scripted Toggle Button state external: only Internal toggles persist a boolean `value` in the document.

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

- Replace text-only Collapsible Folder sections with bordered cards that have a compact header and nested content area.
- Use a small disclosure chevron in the Collapsible Folder header and update it together with the collapsed state.
- Add a subtle left accent to Collapsible Folder headers while keeping nested content visually subordinate.

## 0.3.3

Folder hierarchy polish release.

### Changed

- Keep the main toolbox canvas and folder content background visually continuous instead of drawing separate content cards.
- Use compact uppercase section titles for Simple Section headers.
- Use a subtle header border and a compact left accent for Collapsible Folder titles.
- Reduce nested folder spacing and padding so nested layouts stay compact.

## 0.3.2

Field and compact-row polish release.

### Changed

- Match selection-backed Field controls to the same compact height as String and Menu controls.
- Keep Field text selectable without showing a persistent selection highlight when it is not focused.
- Allow compact Row controls to shrink naturally instead of inheriting full-width runtime minimums.
- Keep fixed-width Row child sizing available for deliberately wide controls.

## 0.3.1

Runtime control consistency release.

### Changed

- Use the same field height for String, Menu, Integer, Float, Color and Field controls.
- Match checkbox vertical alignment to neighboring field controls.
- Remove redundant top-level runtime margins and tighten Folder content spacing.
- Keep nested folder indentation while reducing unnecessary empty space.

## 0.3.0

Interface layout and control release.

### Added

- Add typed interface controls for String, Integer, Float, Checkbox, Menu, Color, Field, Label, Separator and Row.
- Add Folder display types: Collapsible, Simple Section, Tabs and Radio Buttons.
- Add drag-and-drop reordering in the Interface Editor.
- Add per-item display labels, tooltips and row-width settings.
- Add selection-backed Field controls with scene selection support.

### Changed

- Replace the legacy flat folder/button editor with a typed interface model and runtime renderer.
- Upgrade the config schema to version 15 with backward compatibility for legacy button/folder data.

## 0.2.0

Modular architecture release.

### Added

- Split the original single-file Script Toolbox into a modular package.
- Add Maya, Nuke and Houdini host adapters behind a common host interface.
- Add updater support, config backup/recovery and release packaging.

### Changed

- Move runtime UI, model, config, host integrations and update logic into separate modules.
- Keep compatibility with Maya 2015 / Python 2.7 while supporting modern Python hosts.

## 0.1.0

Initial modular release.

### Added

- Add the Script Toolbox runtime window and JSON configuration.
- Add script buttons with Python/MEL execution and Shift+Click alternate actions.
- Add the Interface Editor for creating and arranging toolbox controls.
