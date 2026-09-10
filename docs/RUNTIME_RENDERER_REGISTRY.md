# Runtime Renderer Registry

The runtime renderer registry is the active dispatch mechanism for Script Toolbox item widgets.

## Boundary

`core.runtime_registry.RuntimeRendererRegistry` is a Qt-independent mapping from an item `kind` to a renderer callable. The core registry does not import Maya, Nuke, Qt, the Interface Editor or parameter-reference rewriting.

UI renderers live in `ui.runtime_renderers` and the specialized Row, Column, Toggle Button and Toggle Icon renderer modules.

`RuntimeFolder.build_runtime_widget()` reads the active registry directly. UI initialization creates the registry before the runtime main window is imported and then registers specialized current kinds.

There is no stored legacy renderer path and no runtime replacement of `RuntimeFolder.build_runtime_widget()`.

## Current kinds

The default/specialized registry covers the current renderable item set:

- `folder`
- `row`
- `column`
- `button`
- `toggle_button`
- `icon`
- `toggle_icon`
- `checkbox`
- `field`
- `label`
- `separator`
- `string`
- `integer`
- `float`
- `menu`
- `color`

The removed `toggle` kind is not registered. Unknown model kinds are rejected during item construction rather than silently converted to another kind.

## Renderer contract

A renderer is a callable with this shape:

```python
def render(owner, item, compact=False):
    return widget
```

`owner` is the `RuntimeFolder` responsible for the item. `compact=True` means the item is rendered inside a compact layout context such as a Row.

## Registration

The UI package exposes session-local registration helpers:

```python
from script_toolbox.ui import register_runtime_renderer

register_runtime_renderer(
    "custom_kind",
    render_custom_kind
)
```

Duplicate registration is rejected unless `replace=True` is explicitly supplied. `unregister_runtime_renderer(kind)` removes a registration.

A real new item kind must also define its model factory/schema behavior and, when editable, its property editor. The renderer registry alone does not bypass model validation.

## Event integration

Runtime renderers build widgets; event semantics remain separate. `ui.event_binding_hooks` decorates eligible rendered controls with mouse/editing/selection event filters and dispatches through the single bindings system.

Toggle Button and Toggle Icon renderers only create/register their widgets. Stateful execution and refresh live in the main runtime API rather than being installed by renderer-specific monkey patches.

## Parameter links

Parameter-link remapping is intentionally separate from renderer dispatch.

`core.references` and `EditorDocumentController` own managed Python references during rename, duplicate and paste. Renderers receive the already-normalized current item payload and never rewrite script references or identity fields.
