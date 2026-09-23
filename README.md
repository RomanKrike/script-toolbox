# Script Toolbox

Configurable script toolbox for Maya, Nuke, and Houdini.

**Documentation:** https://romankrike.github.io/script-toolbox/

Current host targets:

- Maya 2015+ — PySide / Qt 4 on Maya 2015–2016, PySide2 / Qt 5 on Maya 2017–2024, and PySide6 / Qt 6 on Maya 2025+; Python + MEL
- Nuke 12+ — PySide2 / Qt 5 on Nuke 12–15 and PySide6 / Qt 6 on Nuke 16+; Python
- Houdini 19+ — PySide2 / Qt 5 on Houdini 19–20.x; Houdini 20.5 also has optional Qt 6 / PySide6 builds; Houdini 21 defaults to Qt 6 / PySide6 while separate Qt 5 builds remain supported; Houdini 22+ is Qt 6 / PySide6; Python + HScript

The UI keeps one shared widget tree across these hosts. A compatibility layer resolves the Qt/PySide generation at runtime, honors Houdini's host binding preference, and preserves the legacy QtGui-style widget API used by the Maya 2015 codebase.

## Architecture status

The active implementation lives under:

```text
scripts/script_toolbox/
```

Script Toolbox currently uses **config schema 21 as the single supported document contract**. Earlier schemas are intentionally not converted while the plugin remains under active development. A non-empty config must declare the current schema version.

The model/core is Maya-independent. Runtime and Interface Editor use the same item factories, container traversal, reference rules and event-binding model. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the dependency and schema contracts.

## Maya entry point

With the repository installed as a Maya module:

```python
import script_toolbox
script_toolbox.show()
```

During development:

```python
import script_toolbox
script_toolbox.reload_toolbox()
```

The repository contains `MayaScriptToolbox.mod` for Maya module-based installation.

## Nuke entry point

Inside Nuke:

```python
import script_toolbox
script_toolbox.show()
```

Register the Nuke application menu:

```python
import script_toolbox
script_toolbox.register_nuke_menu()
```

Register the dockable Nuke panel:

```python
import script_toolbox
script_toolbox.register_nuke_panel()
```

See [docs/NUKE.md](docs/NUKE.md) and `nuke/menu.py.example` for installation.

## Houdini entry point

Point Houdini at the repository `scripts` directory through `PYTHONPATH`, then run:

```python
import script_toolbox
script_toolbox.show()
```

During development:

```python
import script_toolbox
script_toolbox.reload_toolbox()
```

See [docs/HOUDINI.md](docs/HOUDINI.md) and `houdini/script_toolbox.json.example` for the Houdini package setup.

## Current feature set

- Folder containers: Collapsible, Simple, Tabs and Radio
- Row and Column layout containers
- Button and dedicated Toggle Button actions
- Icon and dedicated Toggle Icon actions
- String, Integer, Float, Checkbox, Menu, Color and Field values
- Label, Text, Image and Separator presentation/display items
- scalar and vector numeric controls with optional sliders
- per-item `bindings` for click, double-click, value and editing events supported by each kind
- Python / MEL / HScript event scripts according to the active host
- stable item `id` plus script-facing symbolic `name`; `label` is presentation text only
- nested reference rewriting for rename, duplicate, copy and paste
- embedded code editor with Script Toolbox API autocomplete
- DCC-aware reusable Presets plus JSON Import / Export
- persistent parameter values and config backup/recovery
- Interface Editor Undo / Redo, Duplicate, Copy and Paste
- Field List mode with multi-selection, copy, double-click scene selection and configurable visible rows
- Field collection API: `get_field_selection`, `add_to_field`, `remove_from_field`, `clear_field`
- encrypted config/item sharing through the share-provider abstraction
- shared HTTP transport with System / Manual proxy support for HTTP, HTTPS and SOCKS5
- Stable / Development update channels

## Config contract

New documents are written with:

```json
{
  "version": 21,
  "sections": []
}
```

Only schema 21 is accepted by the current build. Older, newer, invalid and non-empty versionless documents are rejected rather than inferred or converted. An empty mapping is accepted internally only when creating a brand-new configuration.

Event behavior is persisted only in `bindings`. Callback dictionaries and direct script fields are not part of the current schema.

Config paths are resolved centrally by `core/user_paths.py`. Stable and Development builds use the same host user-config directory; there is no separate test/dev config path. In Maya the canonical files are `maya_script_toolbox.json` and `script_toolbox_settings.json` under Maya's user preferences directory. Runtime config/settings paths are not overridden by environment variables.

## Continuous integration

Every push and pull request runs GitHub Actions checks covering:

- unit tests on Python 3.8 and Python 3.11;
- coverage for Maya-independent model/core code;
- flake8 correctness checks;
- package compilation;
- Maya 2015 / Python 2.7 compile and smoke checks;
- Nuke host import, config I/O, execution, updater, controls and encrypted-share Python 2.7 smoke checks;
- Qt binding-generation and legacy API compatibility tests;
- release-package contract tests;
- a downloadable test-build artifact after all required checks pass.

Regression tests cover the current schema, nested Folder/Row/Column traversal, item factories, bindings, reference rewriting, runtime values, editor command history, updater behavior and package construction.

## Updates and releases

Script Toolbox checks GitHub Releases using the selected update channel. Stable releases come from `main`; development builds come from `dev` through the dedicated development workflow.

A stable release is created only after the accumulated `dev` changes are tested and intentionally merged into `main`. The release version follows SemVer according to the actual contents of that release; development commits do not create individual releases.

The updater downloads and verifies release archives, preserves the user configuration, replaces the installed plugin package, then attempts a hot reload. A host restart is only the fallback if hot reload cannot complete safely.

The repository is public, so normal update checks do not require credentials. `SCRIPT_TOOLBOX_GITHUB_TOKEN` remains supported for private forks and is never stored in the toolbox configuration.
