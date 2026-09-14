# -*- coding: utf-8 -*-
from __future__ import print_function

from ..model.item_view import ItemDataView
from ..model.item_view import item_view
from .runtime import build_folder_widgets


def _raw_item(value):
    if isinstance(value, ItemDataView):
        return value.raw()
    return value


def build_item_aware_toolbox_class(base_class):
    """Adapt document Items to the universal envelope view at runtime edges."""

    class ItemAwareToolbox(base_class):
        def all_items(self):
            for item in base_class.all_items(self):
                yield item_view(item)

        def find_item(self, key):
            item = base_class.find_item(self, key)
            return item_view(item) if item is not None else None

        def dispatch_binding_event(
            self,
            item_or_id,
            event,
            value=None,
            old_value=None,
            mouse_button=None,
            modifiers=None
        ):
            return base_class.dispatch_binding_event(
                self,
                _raw_item(item_or_id),
                event,
                value=value,
                old_value=old_value,
                mouse_button=mouse_button,
                modifiers=modifiers
            )

        def rebuild(self):
            self.field_widgets = {}
            self.state_button_widgets = {}
            self.toggle_icon_widgets = {}

            while self.content_layout.count() > 1:
                layout_item = self.content_layout.takeAt(0)
                widget = layout_item.widget()
                if widget is not None:
                    widget.deleteLater()

            sections = [
                item_view(section)
                for section in self.config.get("sections", []) or []
                if isinstance(section, dict)
            ]
            widgets = build_folder_widgets(
                self,
                sections,
                self.content
            )
            for widget in widgets:
                self.content_layout.insertWidget(
                    self.content_layout.count() - 1,
                    widget
                )

            self.refresh_selection_fields(force=True)
            self.refresh_state_buttons()

    ItemAwareToolbox.__name__ = "ItemAware{0}".format(base_class.__name__)
    return ItemAwareToolbox


__all__ = [
    "build_item_aware_toolbox_class",
]
