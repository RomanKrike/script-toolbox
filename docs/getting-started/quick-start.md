# Quick start

This walkthrough covers the normal Script Toolbox workflow: open the toolbox, edit its structure, add an item, attach behavior, and return to runtime mode.

## 1. Open Script Toolbox

From the host Python console:

```python
import script_toolbox
script_toolbox.show()
```

The runtime window displays the current toolbox configuration.

## 2. Open the Interface Editor

Switch to the Interface Editor to modify the toolbox structure. The editor works on the same document model used by runtime, so the interface you build is the interface the toolbox renders.

## 3. Add structure

Start with a container when you need grouping or layout. Available structures include:

- Collapsible, Simple, Tabs, and Radio folders;
- Row layouts;
- Column layouts.

Containers can be nested to build compact tool panels.

## 4. Add an item

Add an item such as a Button, Field, Checkbox, Menu, Label, or Icon. Configure its presentation properties and, when applicable, its script-facing `name`.

Each item has a stable internal `id`. The `name` is the symbolic identifier intended for scripts; `label` is presentation text only.

## 5. Add behavior

Interactive items expose supported event bindings. Depending on the item, these can include click, double-click, value-change, or editing events.

Attach a script to the required binding. Script language support depends on the host:

| Host | Languages |
| --- | --- |
| Maya | Python, MEL |
| Nuke | Python |
| Houdini | Python, HScript |

## 6. Test in runtime

Save the configuration and return to runtime mode. Exercise the new control and verify both the visual result and the script behavior.

## 7. Iterate safely

The Interface Editor supports Undo/Redo, Duplicate, Copy, and Paste. When nested items are duplicated or renamed, Script Toolbox rewrites supported internal references so copied structures can remain self-contained.

## Next steps

- [Understand the editor and runtime workflow](../guide/interface.md)
- [Browse the available item types](../guide/items.md)
- [Learn the scripting model](../guide/scripting.md)
- [Share a toolbox or item](../guide/sharing-updates.md)
