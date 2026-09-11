# Items

Script Toolbox builds interfaces from containers, interactive controls, value controls, and presentation items.

## Containers

| Item | Purpose |
| --- | --- |
| Collapsible Folder | Group controls in an expandable section |
| Simple Folder | Group controls without collapsible behavior |
| Tabs Folder | Split content into tabs |
| Radio Folder | Switch between mutually exclusive sections |
| Row | Arrange child items horizontally |
| Column | Arrange content in columns |

## Actions

| Item | Purpose |
| --- | --- |
| Button | Run an action from a text button |
| Toggle Button | Run state-aware toggle behavior from a button |
| Icon | Run an action from an icon control |
| Toggle Icon | Icon equivalent of a toggle action |

Interactive actions can expose bindings such as click or double-click depending on the item kind.

## Value controls

| Item | Purpose |
| --- | --- |
| String | Text value |
| Integer | Integer numeric value |
| Float | Floating-point numeric value |
| Checkbox | Boolean state |
| Menu | Choice from a predefined set |
| Color | Color value |
| Field | Text/object field with optional list behavior |

Numeric controls support scalar/vector variants where applicable and can optionally expose sliders.

## Field list mode

Field can operate as a list-oriented control for workflows such as scene object collections. List mode supports multiple selection, copy behavior, double-click scene selection, and configurable visible rows.

The scripting API includes helpers for managing Field collections:

```python
get_field_selection(...)
add_to_field(...)
remove_from_field(...)
clear_field(...)
```

Use Field list mode when the control needs to represent a changing collection rather than a single text value.

## Presentation items

| Item | Purpose |
| --- | --- |
| Label | Display non-interactive text |
| Separator | Add visual spacing or separation |

Presentation items are useful for explanations, grouping, and making larger toolboxes easier to scan.

## Event bindings

Each interactive item exposes only the events supported by that item kind. These can include:

- click;
- double-click;
- value change;
- editing-related events.

Behavior is stored in per-item `bindings`, keeping presentation properties separate from executable behavior.
