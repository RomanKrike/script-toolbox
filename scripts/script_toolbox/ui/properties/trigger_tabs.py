# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtCore
from ...compat import QtGui
from . import base as base_module
from . import bindings as bindings_module


_BaseBindingPanel = bindings_module.BindingPanel


class TriggerTabBindingPanel(_BaseBindingPanel):
    """Binding panel whose add action is a real trailing tab.

    The legacy panel used QTabWidget.setCornerWidget(), which leaves '+' as a
    visually separate tool button. Keep the existing binding behavior, but
    expose Add Trigger as the final tab so it belongs to the trigger strip.
    """

    def __init__(
        self,
        toolbox=None,
        parent=None
    ):
        self._add_tab_page = None
        _BaseBindingPanel.__init__(
            self,
            toolbox=toolbox,
            parent=parent
        )

        # Remove the legacy corner button. It is deliberately kept out of the
        # layout instead of restyling it, so there is only one visible Add UI.
        try:
            self.tabs.setCornerWidget(
                None,
                QtCore.Qt.TopRightCorner
            )
        except Exception:
            pass

        try:
            self.add_button.hide()
            self.add_button.deleteLater()
        except Exception:
            pass
        self.add_button = None

        self._ensure_add_tab()

    def _hide_add_tab_close_button(self, index):
        bar = self.tabs.tabBar()
        for side in (
            QtGui.QTabBar.LeftSide,
            QtGui.QTabBar.RightSide,
        ):
            try:
                button = bar.tabButton(
                    index,
                    side
                )
                if button is not None:
                    button.hide()
                bar.setTabButton(
                    index,
                    side,
                    None
                )
            except Exception:
                pass

    def _ensure_add_tab(self):
        if (
            self._add_tab_page is not None and
            self.tabs.indexOf(self._add_tab_page) >= 0
        ):
            return

        self._add_tab_page = QtGui.QWidget(
            self.tabs
        )
        self._add_tab_page.setObjectName(
            "AddTriggerTabPage"
        )
        index = self.tabs.addTab(
            self._add_tab_page,
            "+"
        )
        self.tabs.setTabToolTip(
            index,
            "Add trigger"
        )
        self._hide_add_tab_close_button(
            index
        )

    def _remove_add_tab(self):
        if self._add_tab_page is None:
            return

        index = self.tabs.indexOf(
            self._add_tab_page
        )
        if index >= 0:
            self.tabs.removeTab(
                index
            )

    def clear(self):
        _BaseBindingPanel.clear(
            self
        )
        self._add_tab_page = None
        self._ensure_add_tab()

    def _add_page(self, binding):
        # Real trigger tabs must always stay before the trailing '+' tab.
        self._remove_add_tab()
        try:
            return _BaseBindingPanel._add_page(
                self,
                binding
            )
        finally:
            self._ensure_add_tab()

    def eventFilter(self, watched, event):
        if watched is self.tabs.tabBar():
            if event.type() == QtCore.QEvent.MouseButtonPress:
                index = watched.tabAt(
                    event.pos()
                )
                add_index = len(
                    self.pages
                )

                if index == add_index:
                    try:
                        if event.button() != QtCore.Qt.LeftButton:
                            return True
                    except Exception:
                        pass

                    # Do not select the dummy page. Open the existing dialog
                    # after the mouse event finishes instead.
                    QtCore.QTimer.singleShot(
                        0,
                        self.add_binding
                    )
                    return True

        return _BaseBindingPanel.eventFilter(
            self,
            watched,
            event
        )


def install_integrated_trigger_tabs():
    """Route PropertyEditorBase to the integrated trigger-tab panel."""
    bindings_module.BindingPanel = TriggerTabBindingPanel
    base_module.BindingPanel = TriggerTabBindingPanel


__all__ = [
    "TriggerTabBindingPanel",
    "install_integrated_trigger_tabs",
]
