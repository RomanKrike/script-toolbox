# Runtime Renderer Registry

STEP 09 moves active runtime control dispatch behind a registry without changing the JSON schema or item payload semantics.

## Boundary

`core.runtime_registry.RuntimeRendererRegistry` is a Qt-independent mapping from an item `kind` to a renderer callable. The core registry does not import Maya, Nuke, Qt, the Interface Editor, or parameter-reference rewriting.

UI renderers live in `ui.runtime_renderers`. They reuse the existing `RuntimeFolder` helper methods and reproduce the current widget behavior while the legacy `ui.runtime` implementation remains available as a compatibility layer.

The active `RuntimeFolder.build_runtime_widget()` path is installed through the registry when `script_toolbox.ui` is imported. This happens before `main_window` imports and starts constructing runtime folders.

## Default kinds

The registry currently installs the complete existing runtime set:

- `folder`
- `row`
- `button`
- `toggle` (legacy compatibility)
- `checkbox`
- `field`
- `label`
- `separator`
- `string`
- `integer`
- `float`
- `menu`
- `color`

An unknown kind preserves the previous behavior and returns no runtime widget.

## Renderer contract

A renderer is a callable with this shape:

```python
def render(owner, item, compact=False):
    # owner is the RuntimeFolder responsible for the item.
    # Return a QWidget-compatible object or None.
    return widget
```

`compact=True` means the item is being rendered inside a Row and should preserve the existing compact layout semantics.

## Registration

The UI package exposes session-local registration helpers:

```python
from script_toolbox.ui import register_runtime_renderer

register_runtime_renderer(
    "vector3",
    render_vector3
)
```

Duplicate registration is rejected unless `replace=True` is explicitly supplied. `unregister_runtime_renderer(kind)` removes a registration. Runtime registrations are process/session state; development reload and installed hot reload rebuild the default registry, so external registrations must be installed again after a reload.

The extension API is an architectural seam for upcoming control types. It does not bypass model normalization or introduce schema fields by itself. New controls still need their model/default/property-editor work in the roadmap feature that introduces them.

## Parameter links

Parameter-link remapping is intentionally separate from renderer dispatch.

`core.references` and `EditorDocumentController` own managed script references during rename, duplicate and paste. Runtime renderers receive the already-defined item payload and must not rewrite script references or technical names. This separation keeps the new link behavior independent from runtime widget creation and prevents renderer plugins from accidentally changing editor link semantics.

## Compatibility strategy

The large legacy `RuntimeFolder.build_runtime_widget()` if-chain remains in `ui.runtime` for now, but the active routed class method is replaced with registry dispatch during UI package initialization. Keeping the old method as a stored compatibility implementation minimizes risk for Maya 2015 / PySide1 while allowing the new architecture to be tested and extended incrementally.

A later cleanup may physically remove the inactive dispatch chain after enough host-level validation. That cleanup is not part of STEP 09.
