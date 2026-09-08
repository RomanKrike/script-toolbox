# Controls v2

STEP 13 extends Script Toolbox primitives instead of adding a separate model kind for every DCC workflow.

## Schema

Controls v2 uses config schema 17. Schema 16 `on_change_script` values migrate to `callbacks.on_change`. Plugin version remains unchanged by this development step.

## Icons

`icon` is a standalone item with:

- `path`
- `width` / `height`
- `alignment`: `left`, `center`, `right`
- `tooltip`
- `clickable`
- optional Python `callbacks.on_click`

Runtime paths expand environment variables and `~`. A missing image renders a visible fallback marker rather than crashing the toolbox.

Buttons retain their existing scripts/state behavior and add:

- `icon_path`
- `icon_size`
- `icon_only`

An icon-only state button remains icon-only after state refreshes.

## Universal callbacks

Callbacks are stored in one mapping:

```json
{
  "callbacks": {
    "on_change": "print(value)"
  }
}
```

Available events depend on the item kind:

- button: `on_click`
- icon: `on_click`
- string/integer/float/checkbox/menu/color: `on_change`
- field: `on_change`, `on_select`, `on_double_click`
- label: `on_click`
- folder: `on_open`, `on_close`
- row/separator: no runtime events

Callbacks are Python scripts even when a button's primary action is MEL. They execute through `ExecutionResult` diagnostics with this namespace:

- `toolbox`
- `item`
- `value`
- `old_value`
- `event`
- `host`

A per-item/event guard prevents direct recursive callback loops.

### Reference links

Managed Script Toolbox references inside callback code are part of the existing Links system. Rename, duplicate and paste can therefore rewrite calls such as:

```python
toolbox.get_value("source")
```

while leaving unrelated string literals unchanged.

## Numeric controls v2

The existing `integer` and `float` kinds now have:

- `size`: 1, 2, 3 or 4
- `component_labels`
- `show_slider`

Size 1 preserves the historical scalar value contract:

```python
12
```

Size 2-4 returns a list:

```python
[1.0, 2.0, 3.0]
```

Values are normalized and clamped component-by-component. Default component labels are X/Y/Z/W, but labels can be customized, for example Width/Height or R/G/B/A.

When `show_slider` is enabled, each component keeps its numeric spin box and receives a synchronized slider. Float sliders map their configured min/max range to an internal integer slider resolution; stored values remain floats.

## Composition instead of specialized kinds

Controls v2 deliberately does not add these model kinds:

- Selection Set
- Node Picker
- File Picker / Folder Picker
- Button Group
- Vector2 / Vector3 / Vector4
- Slider

They are composed from primitives instead:

- File Picker = Row + String + Icon
- Node Picker = Row + String + Icon
- Selection Set = Field + Row + Buttons
- Button Group = Row + Buttons

This keeps the document model small while the runtime renderer registry and universal callbacks provide the extensibility needed for DCC-specific tools.
