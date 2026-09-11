# Interface and workflow

Script Toolbox has two complementary working states: the **runtime toolbox**, where you use the controls you created, and the **Interface Editor**, where you design and configure those controls.

## Runtime

Runtime renders the saved configuration as the working toolbox. Use it for normal production tasks: run actions, edit values, select objects from Fields, switch tabs, and interact with the controls defined in the document.

Runtime and the Interface Editor use the same item model and renderer contracts, which keeps item behavior consistent between editing and use.

## Interface Editor

The editor is where you build the toolbox hierarchy. Typical operations include:

- create containers and controls;
- reorder and nest items;
- edit presentation and behavior properties;
- add event bindings and scripts;
- duplicate reusable blocks;
- copy and paste items;
- undo and redo document edits.

## Structure

Use containers to control organization before adding many individual controls.

**Folders** provide logical grouping. Script Toolbox supports Collapsible, Simple, Tabs, and Radio folder variants.

**Rows** arrange child items horizontally.

**Columns** provide column-based layout for more structured tool panels.

Containers can be nested, allowing a tab to contain rows, a row to contain fields and buttons, or a collapsible section to contain another structured block.

## Names, labels, and IDs

These three concepts serve different purposes:

- `id` — stable internal identity used by the document and reference system;
- `name` — symbolic script-facing name;
- `label` — presentation text shown to the user.

Changing a visible label should not be treated as changing the identity of the control. Use `name` when scripts need to refer to a toolbox item.

## Editing reusable blocks

Duplicate, Copy, and Paste are intended for reusable interface fragments. Supported references inside duplicated or pasted structures are rewritten to the corresponding new items rather than left pointing to the original block.

This is especially useful for repeated groups that contain scripts referring to sibling controls.

## Configuration lifecycle

The editor saves a JSON document. Script Toolbox currently uses a single active configuration schema while the project is under development; unsupported older or newer non-empty schemas are rejected rather than silently guessed or converted.

The user configuration is stored outside the installed plugin package and is preserved by the updater.
