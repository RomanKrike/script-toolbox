# Changelog

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
