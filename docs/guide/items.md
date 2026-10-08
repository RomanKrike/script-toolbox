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

## Color display

Color shows a clickable swatch followed by editable R, G, B and HEX fields.
Click the swatch to open the existing color chooser. In Appearance, **Show RGB**
and **Show HEX** independently hide those fields; **RGB Range** selects `0-1`
or `0-255`. Values in the configuration and Item API always remain three RGB
components in `0-1`. Changing the display range preserves their precision.
HEX represents the same RGB components rounded to eight bits per channel;
editing HEX replaces the value with those components. No color-space conversion
is applied. If both fields are hidden, the swatch remains available.

```python
toolbox.item("tint").set(show_rgb=True, rgb_range="0-255", show_hex=True)
toolbox.item("tint").set(value=[0.25, 0.5, 1.0])
```

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
| Label | Display a short non-interactive label |
| Text | Display multiline explanatory text with word wrapping |
| Image | Display a raster image with contain, cover, or stretch fitting |
| Separator | Add visual spacing or separation |

Presentation items are useful for explanations, grouping, and making larger toolboxes easier to scan.

## Event bindings

Each interactive item exposes only the events supported by that item kind. These can include:

- click;
- double-click;
- value change;
- editing-related events.

Behavior is stored in per-item `bindings`, keeping presentation properties separate from executable behavior.

Images use a framed card. **Show filename** displays the basename of `source` below the image (hidden for an empty source). Long names are shortened with the full name in a tooltip. `width` and `height` describe the image area; the frame and caption add to the total size. Scripts can use `toolbox.item("preview").set(source="/images/view.png", show_filename=True)`.

You can drag an item from **Create Parameters → Items** into **Existing Parameters**. Drop on a Folder, Row or Column to add it inside; drop above or below an item to choose its position. Closed containers expand after a short hover. Invalid destinations are blocked. Dragging from **Presets** creates an editable copy; references remain an explicit context-menu action. Palette drops support Undo/Redo and are saved with Apply/Accept.
