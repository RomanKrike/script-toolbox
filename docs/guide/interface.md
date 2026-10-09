# Interface and workflow

Script Toolbox has two complementary working states: the **runtime toolbox**, where you use the controls you created, and the **Interface Editor**, where you design and configure those controls.

Screenshots below show the actual **standalone 1.1.0** interface with a demo **BEARS** configuration. Window styling can differ in Windows and inside DCC hosts. Click a screenshot to open it at full size.

## Runtime

Runtime renders the saved configuration as the working toolbox. Use it for normal production tasks: run actions, edit values, select objects from Fields, switch tabs, and interact with the controls defined in the document.

Runtime and the Interface Editor use the same item model and renderer contracts, which keeps item behavior consistent between editing and use.

[![Runtime toolbox with shot controls and utility buttons](../assets/images/interface/runtime.png)](../assets/images/interface/runtime.png)

*Runtime: a demo shot selector, project actions and preview controls.*

## Interface Editor

The editor is where you build the toolbox hierarchy. Typical operations include:

- create containers and controls;
- reorder and nest items;
- edit presentation and behavior properties;
- add event bindings and scripts;
- duplicate reusable blocks;
- copy and paste items;
- undo and redo document edits.

[![Interface Editor with item palette, hierarchy and selected Menu properties](../assets/images/interface/editor.png)](../assets/images/interface/editor.png)

*Left: available item types. Center: the staged hierarchy. Right: properties of the selected Shot menu. Apply/Accept commits your changes.*

## Settings

Open **Settings → Open Settings**. Choose a category on the left: General, Appearance, Network, DCC Integrations, Preset Library, Privacy or About.

**Appearance** has a compact theme selector with **+ / -**, Import, Export and Reset at the top. Theme management and the eight UI colors use the same Simple Folder frames as the other Settings pages. Colors appear in one list; their fields share the same width and right alignment. Color changes apply immediately and turn the selected theme into **Custom**, preserving the source theme. **+** creates a named copy; **-** removes the selected user theme and is disabled for built-in themes. **Save** commits the current colors and theme list, including unnamed Custom changes; **Cancel** discards staged copies/deletions and restores the original palette. Import / Export exchange versioned JSON themes containing a name and colors. Reset restores the default Charcoal palette.

[![Settings window showing Network proxy preferences](../assets/images/interface/settings.png)](../assets/images/interface/settings.png)

*Network settings: connection mode, manual proxy fields and connection test.*

[![Preset Library settings with BEARS selected](../assets/images/interface/libraries.png)](../assets/images/interface/libraries.png)

*Preset Library: connected libraries, selected folder, update policy, Check now and Sync now. The network folder shown is illustrative.*

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


## Presets

The **Presets** palette provides reusable Item subtrees that can be inserted into the staged document. Presets are filtered by the active DCC, while presets marked for `all` hosts remain available everywhere.

Built-in presets carry stable metadata (`id`, `dcc`, `category`, `label`, `description`) and an ordinary Script Toolbox Item subtree as `root`. Inserting a preset clones that subtree through the same document controller used by Duplicate and Paste, so IDs/names are regenerated as needed and supported internal script references are rewritten.

Use presets for repeatable tool patterns; use JSON Import/Export when you need to transfer or archive a complete configuration.

[![Presets catalog with Default and BEARS alongside the staged hierarchy](../assets/images/interface/presets.png)](../assets/images/interface/presets.png)

*Create Parameters → Presets: expand a library/category and insert the preset into Existing Parameters. See [Preset libraries](preset-libraries.md) for the full workflow.*

## Configuration lifecycle

The editor saves a JSON document. Ordinary configs use schema **21**; configs containing linked preset references use schema **22** and require Script Toolbox 1.1.0 or later. Other versions and non-empty versionless configs are rejected. Older configs are not migrated automatically. Built-in presets are inserted as local copies; managed library controls remain linked until converted to a local copy. See [Preset libraries](preset-libraries.md).

The user configuration is stored outside the installed plugin package and is preserved by the updater.
