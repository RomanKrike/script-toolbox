# Script Toolbox

Configurable script toolbox for Maya, Nuke, and Houdini.

Current host targets:

- Maya 2015 — Python 2.7, PySide 1 / Qt 4, Python + MEL
- Nuke 12 — Python 2.7, PySide2 / Qt 5, Python
- Houdini 19.0 — Python 3.7 default build, PySide2 / Qt 5, Python + HScript

## Architecture status

The active implementation lives under:

```text
scripts/script_toolbox/
```

Script Toolbox currently uses **config schema 20 as the single supported document contract**. Earlier schemas are intentionally not converted while the plugin remains under active development. A non-empty config must declare the current schema version.

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

## Houdini 19 entry point

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

See [docs/HOUDINI.md](docs/HOUDINI.md) and `houdini/script_toolbox.json.example` for the Houdini 19 package setup.

## Current feature set

- Folder containers: Collapsible, Simple, Tabs and Radio
- Row and Column layout containers
- Button and dedicated Toggle Button actions
- Icon and dedicated Toggle Icon actions
- String, Integer, Float, Checkbox, Menu, Color and Field values
- Label and Separator presentation items
- scalar and vector numeric controls with optional sliders
- per-item `bindings` for click, double-click, value and editing events supported by each kind
- Python / MEL / HScript event scripts according to the active host
- stable item `id` plus script-facing symbolic `name`; `label` is presentation text only
- nested reference rewriting for rename, duplicate, copy and paste
- embedded code editor
- JSON Import / Export
- persistent parameter values and config backup/recovery
- Interface Editor Undo / Redo, Duplicate, Copy and Paste
- Field List mode with multi-selection, copy, double-click scene selection and configurable visible rows
- Field collection API: `get_field_selection`, `add_to_field`, `remove_from_field`, `clear_field`
- encrypted config/item sharing through the share-provider abstraction
- Stable / Latest / Development update channels

## Config contract

New documents are written with:

```json
{
  "version": 20,
  "sections": []
}
```

Only schema 20 is accepted by the current build. Older, newer, invalid and non-empty versionless documents are rejected rather than inferred or converted. An empty mapping is accepted internally only when creating a brand-new configuration.

Event behavior is persisted only in `bindings`. Callback dictionaries and direct script fields are not part of the current schema.

## Continuous integration

Every push and pull request runs GitHub Actions checks covering:

- unit tests on Python 3.8 and Python 3.11;
- coverage for Maya-independent model/core code;
- flake8 correctness checks;
- package compilation;
- Maya 2015 / Python 2.7 compile and smoke checks;
- Nuke host import, config I/O, execution, updater, controls and encrypted-share Python 2.7 smoke checks;
- release-package contract tests;
- a downloadable test-build artifact after all required checks pass.

Regression tests cover the current schema, nested Folder/Row/Column traversal, item factories, bindings, reference rewriting, runtime values, editor command history, updater behavior and package construction.

## Updates and releases

Script Toolbox checks GitHub Releases using the selected update channel. Stable releases come from `main`; development builds come from `dev` through the dedicated development workflow.

A stable release is created only after the accumulated `dev` changes are tested and intentionally merged into `main`. The release version follows SemVer according to the actual contents of that release; development commits do not create individual releases.

The updater downloads and verifies release archives, preserves the user configuration, replaces the installed plugin package, then attempts a hot reload. A host restart is only the fallback if hot reload cannot complete safely.

The repository is public, so normal update checks do not require credentials. `SCRIPT_TOOLBOX_GITHUB_TOKEN` remains supported for private forks and is never stored in the toolbox configuration.
