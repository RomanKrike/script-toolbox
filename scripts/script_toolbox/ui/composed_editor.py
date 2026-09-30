# -*- coding: utf-8 -*-
"""Declared editor composition; method order is visible without executing factories."""
from .editor_document_adapter import ControllerEditorMixin
from .editor_selection_state import EditorSelectionStateMixin
from .interface_editor import InterfaceEditor as InterfaceEditorView
from .preset_hooks import PresetEditorMixin
from .reference_warning_hooks import ReferenceWarningEditorMixin
from .telemetry_hooks import TelemetryEditorMixin, install_telemetry_share_controller
from .template_transfer_hooks import TemplateTransferEditorMixin


class InterfaceEditor(TelemetryEditorMixin, TemplateTransferEditorMixin,
                      PresetEditorMixin, ReferenceWarningEditorMixin,
                      ControllerEditorMixin, EditorSelectionStateMixin,
                      InterfaceEditorView):
    share_controller_factory = staticmethod(install_telemetry_share_controller)


__all__ = ["InterfaceEditor"]
