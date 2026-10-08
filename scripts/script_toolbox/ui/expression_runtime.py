# -*- coding: utf-8 -*-
"""Surface-owned state bindings. No renderer wrapping or widget reconstruction."""
from __future__ import print_function
from ..core.expressions import ExpressionState, PROPERTIES, bind_expression_references


class ConditionManager(object):
    def __init__(self, document):
        self.state = ExpressionState(document)
        self.widgets = {}
        self.document = document
        self.active = True

    def register(self, item, widget, apply=None):
        if widget is None:
            return
        self.widgets[item['id']] = (widget, apply, widget.toolTip())

    def refresh(self, changed_id=None, recompile=False):
        if not self.active:
            return
        if recompile:
            bind_expression_references(self.document)
            self.state = ExpressionState(self.document)
        targets = self.widgets if changed_id is None else self.state.dependents.get(changed_id, ())
        for item_id in list(targets):
            entry = self.widgets.get(item_id)
            if entry is None:
                continue
            widget, apply, base = entry
            visible = self.state.evaluate(item_id, 'visible')
            enabled = self.state.evaluate(item_id, 'enabled')
            if apply is not None:
                apply(visible, enabled)
            else:
                widget.setVisible(visible)
                widget.setEnabled(enabled)
            errors = [prop + ': ' + self.state.errors[(item_id, prop)] for prop in PROPERTIES
                      if (item_id, prop) in self.state.errors]
            widget.setToolTip(base + ('\nExpression: ' + '\n'.join(errors) if errors else ''))

    def dispose(self):
        self.active = False
        self.widgets.clear()
        self.document = self.state = None


class ExpressionRuntimeMixin(object):
    def refresh_expressions(self, key=None, recompile=False):
        surface = getattr(self, 'runtime_surface', None)
        if surface is None:
            return
        item = self.find_item(key) if key is not None else None
        surface.context.conditions.refresh(item['id'] if item else None, recompile=recompile)

    def set_enabled(self, key, enabled):
        return self._set_presentation_state(key, 'enabled', enabled)

    def enable(self, key):
        return self.set_enabled(key, True)

    def disable(self, key):
        return self.set_enabled(key, False)

    def set_visible(self, key, visible):
        return self._set_presentation_state(key, 'visible', visible)

    def _set_presentation_state(self, key, prop, value):
        if not isinstance(value, bool):
            raise ValueError('Presentation state must be bool')
        item = self.find_item(key)
        if item is None:
            from ..model.items import walk_items
            items = list(walk_items(self.config, include_sections=True))
            item = next((candidate for candidate in items if candidate['id'] == key), None)
            if item is None:
                item = next((candidate for candidate in items if candidate['name'] == key), None)
        if item is None:
            return False
        ui = item.setdefault('ui', {})
        ui[prop] = value
        ui[prop + '_expression_enabled'] = False
        self.save()
        self.refresh_expressions(recompile=True)
        return True
