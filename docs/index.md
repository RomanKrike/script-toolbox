# Script Toolbox

**Script Toolbox** is a configurable script launcher and UI builder for **Autodesk Maya, Foundry Nuke, and SideFX Houdini**. Build reusable interfaces from buttons, fields, menus, layout containers, icons, images, labels, and other items, then attach Python or host-specific scripts to them.

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

Script Toolbox supports nested folder containers, rows and columns, tabs, radio groups, buttons and toggle actions, icons, images, text and numeric controls, checkboxes, menus, colors, fields, labels, separators, and event bindings.

Common workflows include:

- personal shelves and production tool launchers;
- compact interfaces for repetitive scene operations;
- reusable selection and object-list tools;
- grouped utilities with tabs, rows, columns, and collapsible sections;
- shared toolbox configurations for a team or another workstation.

## Supported hosts

| Host | Supported generations | Qt / PySide | Script languages |
| --- | --- | --- | --- |
| Maya | Maya 2015+ | PySide / Qt 4 on 2015–2016; PySide2 / Qt 5 on 2017–2024; PySide6 / Qt 6 on 2025+ | Python, MEL |
| Nuke | Nuke 12+ | PySide2 / Qt 5 on 12–15; PySide6 / Qt 6 on 16+ | Python |
| Houdini | Houdini 19+ | PySide2 / Qt 5 on 19–20.x; optional PySide6 / Qt 6 on Houdini 20.5 Qt 6 builds; Houdini 21 main builds use PySide6 / Qt 6 while separate Qt 5.15.2 builds use PySide2; Houdini 22+ uses PySide6 / Qt 6 | Python, HScript |

Script Toolbox uses one shared UI implementation across all supported hosts. The runtime compatibility layer selects the host-appropriate Qt/PySide generation, prefers a binding already loaded or selected by the DCC, and keeps the legacy QtGui-style API used by the original Maya 2015 implementation.

## Documentation map

Start with [Installation](getting-started/installation.md) and [Quick start](getting-started/quick-start.md). The **Guide** section explains the interface, item types, scripting, sharing, and update channels. The **Developer** section exposes the existing implementation documentation for contributors and advanced debugging.

!!! note
    Script Toolbox is under active development. Stable releases are published from `main`; ongoing development is integrated in `dev` before release.
