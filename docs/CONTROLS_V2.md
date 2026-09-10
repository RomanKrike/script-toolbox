# Controls v2

Controls v2 defines the current primitive item set used to compose DCC tools without introducing a specialized model kind for every workflow.

## Schema

Controls v2 uses config schema **20**. Callback dictionaries, direct script fields and earlier config schemas are not translated by the current build.

## Event bindings

`bindings` are the single event contract for interactive items. A binding stores its own event, language, script, mouse button and modifier policy.

Typical public events include:

- Button / Icon / Toggle Button / Toggle Icon: `click`, `double_click`
- String / Integer / Float: `value_changed`, `editing_finished`, `click`, `double_click`
- Checkbox / Menu / Color: `value_changed`, `click`, `double_click`
- Field: `value_changed`, `selection_changed`, `click`, `double_click`
- Label: `click`, `double_click`
- Folder / Row / Column / Separator: no public runtime bindings

Binding scripts execute with the standard runtime namespace including `toolbox`, `item`, `value`, `old_value`, `event` and `host`.

Managed Python references inside binding scripts participate in the Links system, so rename and subtree duplication can rewrite calls such as:

```python
toolbox.get_value("source")
```

without changing unrelated string literals.

## Button and Toggle Button

`button` is action-only. Its appearance can include:

- `icon_path`
- `icon_size`
- `icon_only`
- `color`

Stateful button behavior belongs to the dedicated `toggle_button` kind. Toggle Button supports internal or script-derived state, ON/OFF scripts, labels, colors and the native `state_toggle` binding handler.

## Icon and Toggle Icon

`icon` is a standalone image item with:

- `path`
- `width` / `height`
- `content_alignment`: `left`, `center`, `right`
- `tooltip`
- optional bindings

Runtime paths expand environment variables and `~`. Missing image content renders a visible fallback marker instead of crashing the toolbox.

Stateful icon behavior belongs to `toggle_icon`, which has independent ON/OFF image paths and the same internal/script state model as Toggle Button.

`alignment` and `clickable` are not schema aliases in the current model.

## Numeric controls

The `integer` and `float` kinds support:

- `size`: 1, 2, 3 or 4
- `component_labels`
- `show_slider`

Size 1 stores a scalar. Size 2–4 stores a list. Model construction and runtime value writes use the same numeric normalizer so component count, fallback values and min/max clamping cannot diverge.

Default component labels are X/Y/Z/W but can be customized. When `show_slider` is enabled, each component receives a synchronized slider while the stored value keeps its native integer/float type.

## Composition instead of specialized kinds

Controls v2 deliberately does not add model kinds such as Selection Set, Node Picker, File Picker, Button Group, Vector2/3/4 or Slider.

Those workflows are composed from primitives, for example:

- File Picker = Row + String + Icon
- Node Picker = Row + String + Icon
- Selection Set = Field + Row + Buttons
- Button Group = Row + Buttons

This keeps the document model small while item factories, layout containers, renderer registry and bindings provide the reusable mechanisms.
