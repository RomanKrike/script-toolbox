# Value bindings for custom items

A renderer creates a QWidget. A value binding synchronizes that widget from the
authored item and owns the connections used to write user changes back to the
Toolbox. Neither changes the JSON schema or the item scripting API.

## Contract

Register a `value_binding_factory(root, owner, item)` with a has-value item type
or pass it to `register_runtime_renderer`. The factory runs on the GUI thread
after the renderer returns its root widget. It returns an object with:

- `sync(item)`: update existing controls and return `True` if applied, `False`
  if unsupported. Do not modify the model here. Block control signals when
  setting values that would otherwise emit a user edit.
- `dispose()`: disconnect owned callbacks and release references; safe to call
  repeatedly. Do not disconnect somebody else's callbacks or save configuration.
- `root`: the widget that the binding updates. Subclass `ValueBinding` to get
  signal ownership, an `active` flag and automatic disposal when this root dies.

Use `binding.connect(signal, callback)` for each owned signal. For a user edit,
call `owner.toolbox.store_value(item_id, value)` to use normal validation,
persistence scheduling, state refresh and model-to-UI synchronization.

The Toolbox disposes the previous binding when registering a replacement for
the same item ID, and disposes all bindings before rebuild and on accepted
window close. A synchronization exception is logged with the item ID; the
broken binding is removed and disposed. The model change remains valid and is
not silently reverted. A `False` result retains the binding. A guard prevents
recursive synchronization for the same item; adapters must still block edit
signals to avoid redundant model writes.

Replacing a renderer without supplying a factory clears its previous factory.
Custom has-value renderers without a factory remain renderable but do not gain
automatic value synchronization. Standard Qt controls inside them are never
guessed as targets. Declare a factory when automatic synchronization is needed.
Bindings are local to a rendered item and must not be shared between item IDs.

Built-in item types use typed adapters. Standard-control discovery is confined
to those adapters; field and toggle adapters use their dedicated refresh paths.
Value-edit signal connections made by built-in renderers are transferred to
their binding and disconnected during disposal. Item event dispatch and host
callbacks have separate owners; a binding must not disconnect those wholesale.

## Minimal custom counter

This example runs in a session with Script Toolbox UI loaded. Register the type
once, before adding a `custom_counter` item through the editor. Its widgets are
a label and a button, so synchronization cannot rely on a line edit or spinbox.

```python
from script_toolbox.compat import QtGui
from script_toolbox.model.fields import IntField
from script_toolbox.model.item_registry import ItemTypeDefinition, register_item_type
from script_toolbox.ui import ValueBinding, register_runtime_renderer


class CounterBinding(ValueBinding):
    def __init__(self, root, owner, item):
        ValueBinding.__init__(self, root)
        self.toolbox = owner.toolbox
        self.item_id = item['id']
        self.connect(root.button.clicked, self.increment)

    def increment(self, checked=False):
        value = self.toolbox.get_value(self.item_id)
        self.toolbox.store_value(self.item_id, value + 1)

    def sync(self, item):
        self.root.label.setText(str(item['props']['value']))
        return True

    def dispose(self):
        ValueBinding.dispose(self)
        self.toolbox = None


def render_counter(owner, item, compact=False):
    root = QtGui.QWidget()
    layout = QtGui.QHBoxLayout(root)
    root.label = QtGui.QLabel(str(item['props']['value']))
    root.button = QtGui.QPushButton('+1')
    layout.addWidget(root.label)
    layout.addWidget(root.button)
    return root


register_item_type(ItemTypeDefinition(
    kind='custom_counter', title='Counter',
    fields={'value': IntField(default=0)},
    capabilities=('has_value',),
))
register_runtime_renderer(
    'custom_counter', render_counter,
    value_binding_factory=CounterBinding,
)
```

Alternatively, supply both `renderer` and `value_binding_factory` directly to
`ItemTypeDefinition`. Core definitions store the callables without importing Qt.

Regression coverage: `tests/test_qt_value_bindings.py` tests model/UI updates,
unrelated controls, callback cleanup, renderer replacement without a factory,
binding errors, destroyed roots and reentrant synchronization. The existing
`test_runtime_value_sync.py` covers the typed built-in adapters and signal blocking.
