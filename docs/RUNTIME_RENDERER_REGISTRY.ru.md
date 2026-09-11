# Runtime Renderer Registry

Runtime renderer registry — активный механизм dispatch для widgets элементов Script Toolbox.

## Граница ответственности

`core.runtime_registry.RuntimeRendererRegistry` — независимое от Qt соответствие между `kind` элемента и renderer callable. Core registry не импортирует Maya, Nuke, Qt, Interface Editor или логику переписывания parameter references.

UI renderers находятся в `ui.runtime_renderers` и специализированных renderer-модулях Row, Column, Toggle Button и Toggle Icon.

`RuntimeFolder.build_runtime_widget()` напрямую читает активный registry. UI initialization создаёт registry до импорта runtime main window, затем регистрирует специализированные актуальные kinds.

Вторичного renderer path и runtime-замены `RuntimeFolder.build_runtime_widget()` нет.

## Текущие kinds

Default/specialized registry покрывает текущий набор renderable items:

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

Удалённый kind `toggle` не регистрируется. Неизвестные model kinds отклоняются при создании item вместо молчаливого преобразования в другой kind.

## Контракт renderer

Renderer — callable следующей формы:

```python
def render(owner, item, compact=False):
    return widget
```

`owner` — `RuntimeFolder`, отвечающий за item. `compact=True` означает, что item рендерится внутри compact layout context, например Row.

## Регистрация

UI package предоставляет session-local helpers регистрации:

```python
from script_toolbox.ui import register_runtime_renderer

register_runtime_renderer(
    "custom_kind",
    render_custom_kind
)
```

Повторная регистрация отклоняется, если явно не передан `replace=True`. `unregister_runtime_renderer(kind)` удаляет регистрацию.

Настоящий новый item kind также должен определить model factory/schema behavior и, если он редактируемый, property editor. Один renderer registry не обходит model validation.

## Интеграция событий

Runtime renderers создают widgets; event semantics остаётся отдельным слоем. `ui.event_binding_hooks` добавляет к подходящим rendered controls filters mouse/editing/selection events и dispatch через единую систему bindings.

Renderers Toggle Button и Toggle Icon только создают/регистрируют widgets. Stateful execution и refresh находятся в главном runtime API, а не устанавливаются renderer-specific monkey patches.

## Parameter links

Переназначение parameter links намеренно отделено от renderer dispatch.

`core.references` и `EditorDocumentController` владеют managed Python references при rename, duplicate и paste. Renderers получают уже нормализованный актуальный item payload и никогда не переписывают script references или identity fields.
