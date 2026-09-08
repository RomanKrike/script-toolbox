# Row / Column Layout Contract

`Row` and `Column` are composable layout containers. They can contain normal
controls and other Rows/Columns. `Folder` remains a structural section and is
not a valid child of either layout container.

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

Columns still default to `Stretch` when placed in a Row so sibling columns
share the available width.

## Row

Row owns horizontal placement of its children:

- `Spacing`: gap between children.
- `Horizontal Distribution`: Left, Center, Right, or Space Between.
- `Vertical Alignment`: Top, Center, or Bottom.
- `Equal Widths`: gives every non-separator child the same horizontal share.

A child directly inside a Row owns only its horizontal size:

- `Item Width`: Auto, Stretch, or Fixed.
- `Fixed Width`: used by Fixed.
- `Stretch Weight`: relative share used by Stretch.

`Stretch` describes the size of the item slot in the Row. The child renderer
continues to decide how its internal content uses that slot. This keeps the
layout contract consistent for buttons, fields, numeric controls, labels,
icons, separators, and nested layouts.

`Horizontal Distribution` uses remaining free space. It therefore has no
visible effect while one or more children use `Stretch`, or while
`Equal Widths` consumes the row.

When `Equal Widths` is enabled, the child width controls are disabled in the
Interface Editor to make the parent override explicit.

### Legacy Row alignment

Schema-18 configs may contain `row_alignment` on individual Row children.
The field remains accepted for backward compatibility. When a Row does not
yet contain `horizontal_distribution`, normalization preserves a common
legacy Left/Center/Right value as the new Row distribution when that intent is
unambiguous. The editor no longer exposes per-child horizontal placement.

## Column

Column owns horizontal placement and vertical distribution:

- `Spacing`: vertical gap between children.
- `Child Horizontal Alignment`: Stretch, Left, Center, or Right.
- `Vertical Distribution`: Top, Center, Bottom, or Space Between.

A child directly inside a Column owns its vertical size:

- `Item Height`: Auto, Stretch, or Fixed.
- `Fixed Height`: used by Fixed.
- `Stretch Weight`: relative share used by Stretch.

`Vertical Distribution` uses remaining free space and therefore has no visible
effect while one or more children use Stretch height.

Column child height fields are optional in older JSON. Missing values normalize
to `Auto`, fixed height `28`, and stretch weight `1`.

## Icon content alignment

Standalone Icon alignment is content alignment inside the Icon item, not
placement of the item inside a Row. The editor labels this explicitly as
`Content Alignment`. The legacy `alignment` field remains synchronized for
schema-18 runtime compatibility.

## Compatibility

This refactor is backward compatible with schema 18:

- existing `row_width_mode`, `row_width`, and `row_stretch` remain valid;
- legacy `row_alignment` remains accepted and can seed Row distribution;
- existing Column configs default to Top vertical distribution and Auto child
  heights;
- legacy Icon `alignment` remains supported.

No Folder, callback, binding, or execution semantics are changed.
