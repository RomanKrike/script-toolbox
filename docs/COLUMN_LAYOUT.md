# Column Layout

`Column` is a vertical layout container introduced alongside the existing `Row` layout.

## Composition

Layout containers can be nested to build compact interfaces:

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

`Row` lays children out horizontally. `Column` lays children out vertically. Rows and Columns may contain normal controls and other Rows/Columns. Folders remain section containers and are not valid children of Row/Column.

Columns default to `Stretch` when placed in a Row so sibling columns share available width. The normal Row child width controls can still change a Column to Auto or Fixed width.

## Column properties

- `Spacing`: vertical gap between children.
- `Child Alignment`: Stretch, Left, Center, or Right.

Layout items do not expose event triggers yet. The underlying model keeps layout kinds separate from interactive controls so triggers can be added later without changing the composition model.
