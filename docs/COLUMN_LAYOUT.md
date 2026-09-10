# Row / Column Layout Contract

`Row` and `Column` are composable layout containers. They can contain normal controls and other Rows/Columns. `Folder` remains a structural section and is not a valid child of either layout container.

```text
Row
├── Column
│   ├── Field
│   └── Row
│       ├── Button
│       └── Button
└── Column
    ├── Field
    └── Row
        ├── Button
        └── Button
```

Columns default to `Stretch` when placed in a Row so sibling columns share available width.

## Row

Row owns horizontal placement of its children:

- `Spacing`: gap between children.
- `Horizontal Distribution`: Left, Center, Right, or Space Between.
- `Vertical Alignment`: Top, Center, or Bottom.
- `Equal Widths`: gives every non-separator child the same horizontal share.

A child directly inside a Row owns its horizontal size:

- `Item Width`: Auto, Stretch, or Fixed.
- `Fixed Width`: used by Fixed.
- `Stretch Weight`: relative share used by Stretch.

`Horizontal Distribution` consumes remaining free space. It therefore has no visible effect while a child uses Stretch or while Equal Widths consumes the Row.

When Equal Widths is enabled, child width controls are disabled in the Interface Editor because the parent owns that sizing decision.

## Column

Column owns horizontal placement and vertical distribution:

- `Spacing`: vertical gap between children.
- `Child Horizontal Alignment`: Stretch, Left, Center, or Right.
- `Vertical Distribution`: Top, Center, Bottom, or Space Between.

A child directly inside a Column owns its vertical size:

- `Item Height`: Auto, Stretch, or Fixed.
- `Fixed Height`: used by Fixed.
- `Stretch Weight`: relative share used by Stretch.

`Vertical Distribution` consumes remaining free space and therefore has no visible effect while one or more children use Stretch height.

Current-schema Column children normalize explicit height metadata to the supported modes and bounds. There is no older-schema fallback contract.

## Icon content alignment

Standalone Icon/Toggle Icon alignment is content alignment inside the item, not placement of the item inside a Row or Column.

The schema key is only:

```text
content_alignment = left | center | right
```

`alignment` is not an alias in schema 20.

## Current-schema rules

- `folder`, `row` and `column` share the model container predicate;
- Row/Column may nest Row/Column and leaf items;
- Folder cannot be nested inside Row/Column;
- `row_width_mode`, `row_width` and `row_stretch` describe Row child sizing;
- `column_height_mode`, `column_height` and `column_stretch` describe Column child sizing;
- parent distribution/alignment is explicit and not inferred from historical per-child alignment fields;
- layout containers do not expose public runtime event bindings.
