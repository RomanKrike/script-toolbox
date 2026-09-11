# Script Toolbox

**Script Toolbox** is a configurable script launcher and UI builder for **Autodesk Maya, Foundry Nuke, and SideFX Houdini**. Build reusable interfaces from buttons, fields, menus, layout containers, icons, labels, and other items, then attach Python or host-specific scripts to them.

<div class="stx-grid" markdown>

<div class="stx-card" markdown>
### Install
Download a release, connect Script Toolbox to your host, and open the toolbox.

[Installation guide](getting-started/installation.md)
</div>

<div class="stx-card" markdown>
### Build an interface
Create sections and items in the Interface Editor, configure bindings, then switch back to the runtime toolbox.

[Quick start](getting-started/quick-start.md)
</div>

<div class="stx-card" markdown>
### Script it
Use Python, MEL, or HScript according to the active host. Items expose stable IDs and script-facing symbolic names.

[Scripting guide](guide/scripting.md)
</div>

</div>

## What you can build

Script Toolbox supports nested folder containers, rows and columns, tabs, radio groups, buttons and toggle actions, icons, text and numeric controls, checkboxes, menus, colors, fields, labels, separators, and event bindings.

Common workflows include:

- personal shelves and production tool launchers;
- compact interfaces for repetitive scene operations;
- reusable selection and object-list tools;
- grouped utilities with tabs, rows, columns, and collapsible sections;
- shared toolbox configurations for a team or another workstation.

## Supported hosts

| Host | Baseline | Script languages |
| --- | --- | --- |
| Maya | Maya 2015, Python 2.7, PySide 1 / Qt 4 | Python, MEL |
| Nuke | Nuke 12, Python 2.7, PySide2 / Qt 5 | Python |
| Houdini | Houdini 19.0 default Python 3.7 build, PySide2 / Qt 5 | Python, HScript |

## Documentation map

Start with [Installation](getting-started/installation.md) and [Quick start](getting-started/quick-start.md). The **Guide** section explains the interface, item types, scripting, sharing, and update channels. The **Developer** section exposes the existing implementation documentation for contributors and advanced debugging.

!!! note
    Script Toolbox is under active development. Stable releases are published from `main`; ongoing development is integrated in `dev` before release.
