# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..pycompat import text_type
from ..telemetry.events import track_product_event
from .share_hooks import ShareController


_EDITOR_MARKER = "_script_toolbox_product_telemetry_editor"
_TOOLBOX_MARKER = "_script_toolbox_product_telemetry_toolbox"

_IMPORT_MODE_KEYS = (
    ("Replace Toolbox", "replace"),
    ("Append to Toolbox", "append"),
    ("Insert into Selected Folder", "insert"),
)


def _status_text(editor):
    try:
        return text_type(
            editor.status.text() or ""
        )
    except Exception:
        return ""


def _tree_item_kind(editor, tree_item):
    if tree_item is None:
        return ""
    try:
        return text_type(
            editor.item_data(
                tree_item,
                QtCore.Qt.UserRole
            ) or ""
        ).strip().lower()
    except Exception:
        return ""


class TelemetryShareController(ShareController):
    """Share controller that records only successful semantic operations."""

    def __init__(self, editor):
        self._telemetry_next_share_type = None
        self._telemetry_share_workers = {}
        ShareController.__init__(
            self,
            editor
        )

    def _start_share_operation(
        self,
        status_text,
        operation,
        callback
    ):
        share_type = self._telemetry_next_share_type
        ShareController._start_share_operation(
            self,
            status_text,
            operation,
            callback
        )

        if share_type and self._share_workers:
            worker = self._share_workers[-1]
            self._telemetry_share_workers[
                worker
            ] = share_type

    def _share_operation_finished(
        self,
        worker,
        result
    ):
        share_type = self._telemetry_share_workers.pop(
            worker,
            None
        )
        succeeded = bool(
            result.get("ok")
        )

        ShareController._share_operation_finished(
            self,
            worker,
            result
        )

        if succeeded and share_type:
            track_product_event(
                "share_created",
                {
                    "share_type": share_type,
                }
            )

    def share_settings(self):
        self._telemetry_next_share_type = "config"
        try:
            return ShareController.share_settings(
                self
            )
        finally:
            self._telemetry_next_share_type = None

    def share_selected(self, target_item=None):
        self._telemetry_next_share_type = "item"
        try:
            return ShareController.share_selected(
                self,
                target_item
            )
        finally:
            self._telemetry_next_share_type = None

    def _shared_settings_ready(self, payload):
        result = ShareController._shared_settings_ready(
            self,
            payload
        )
        if _status_text(self.editor).startswith(
            "Pasted shared toolbox ("
        ):
            track_product_event(
                "share_pasted",
                {
                    "share_type": "config",
                }
            )
        return result

    def _shared_item_ready(self, payload):
        result = ShareController._shared_item_ready(
            self,
            payload
        )
        if _status_text(self.editor).startswith(
            "Pasted shared parameter:"
        ):
            track_product_event(
                "share_pasted",
                {
                    "share_type": "item",
                }
            )
        return result


def install_telemetry_share_controller(editor):
    """Install telemetry-aware share composition before editor UI wiring."""
    controller = getattr(
        editor,
        "share_controller",
        None
    )

    if isinstance(
        controller,
        TelemetryShareController
    ):
        return controller

    if controller is not None:
        # Never replace an already-wired controller because Qt signals may hold
        # bound methods from that instance. Active composition calls this
        # installer before build_ui(), so this is only a reload safety guard.
        return controller

    controller = TelemetryShareController(
        editor
    )
    editor.share_controller = controller
    return controller


def build_telemetry_interface_editor_class(base_class):
    """Wrap the final Interface Editor with semantic product events."""
    if getattr(
        base_class,
        _EDITOR_MARKER,
        False
    ):
        return base_class

    class TelemetryInterfaceEditor(base_class):

        def __init__(self, toolbox, parent=None):
            base_class.__init__(
                self,
                toolbox,
                parent=parent
            )
            track_product_event(
                "editor_opened"
            )

        def create_from_palette(
            self,
            palette_item,
            column=0
        ):
            kind = self.palette_item_kind(
                palette_item
            )
            result = base_class.create_from_palette(
                self,
                palette_item,
                column
            )
            if kind:
                track_product_event(
                    "item_created",
                    {
                        "item_type": kind,
                    }
                )
            return result

        def duplicate_selected(
            self,
            target_item=None
        ):
            current = target_item or self.tree.currentItem()
            kind = _tree_item_kind(
                self,
                current
            )
            valid = False
            if current is not None:
                try:
                    item_id = self.item_data(
                        current,
                        QtCore.Qt.UserRole + 1
                    )
                    valid = self.item_cache.get(
                        item_id
                    ) is not None
                except Exception:
                    valid = False

            result = base_class.duplicate_selected(
                self,
                target_item
            )
            if valid and kind:
                track_product_event(
                    "item_duplicated",
                    {
                        "item_type": kind,
                    }
                )
            return result

        def export_settings(self):
            before = _status_text(
                self
            )
            result = base_class.export_settings(
                self
            )
            after = _status_text(
                self
            )
            if (
                after != before and
                after.startswith("Exported:")
            ):
                track_product_event(
                    "config_exported"
                )
            return result

        def import_settings(self):
            before = _status_text(
                self
            )
            result = base_class.import_settings(
                self
            )
            after = _status_text(
                self
            )

            if (
                after == before or
                not after.startswith("Imported ")
            ):
                return result

            for label, mode in _IMPORT_MODE_KEYS:
                marker = "({0})".format(
                    label
                )
                if marker in after:
                    track_product_event(
                        "config_imported",
                        {
                            "mode": mode,
                        }
                    )
                    break

            return result

    TelemetryInterfaceEditor.__name__ = "InterfaceEditor"
    setattr(
        TelemetryInterfaceEditor,
        _EDITOR_MARKER,
        True
    )
    return TelemetryInterfaceEditor


def install_toolbox_telemetry(toolbox_class):
    """Track successful dispatch of explicit runtime item click actions."""
    if getattr(
        toolbox_class,
        _TOOLBOX_MARKER,
        False
    ):
        return toolbox_class

    original = toolbox_class.dispatch_binding_event

    def dispatch_binding_event(
        self,
        item_or_id,
        event,
        *args,
        **kwargs
    ):
        item = (
            item_or_id
            if isinstance(item_or_id, dict)
            else self.find_item(item_or_id)
        )
        kind = text_type(
            item.get("kind", "")
            if isinstance(item, dict)
            else ""
        ).strip().lower()

        result = original(
            self,
            item_or_id,
            event,
            *args,
            **kwargs
        )

        if (
            text_type(event or "").strip().lower() == "click" and
            kind
        ):
            track_product_event(
                "item_activated",
                {
                    "item_type": kind,
                }
            )

        return result

    toolbox_class.dispatch_binding_event = dispatch_binding_event
    setattr(
        toolbox_class,
        _TOOLBOX_MARKER,
        True
    )
    return toolbox_class


__all__ = [
    "TelemetryShareController",
    "build_telemetry_interface_editor_class",
    "install_telemetry_share_controller",
    "install_toolbox_telemetry",
]
