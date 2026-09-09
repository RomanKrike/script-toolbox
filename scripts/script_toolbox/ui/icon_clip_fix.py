# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..style.builtin_icons import builtin_icon
from .painted_icon_button import PaintedIconButton
from .properties.trigger_tabs import TriggerTabBindingPanel


_INSTALL_MARKER = "_script_toolbox_icon_clip_fix_installed"


def _install_trigger_close_button(self, page):
    if page not in self.pages:
        return

    index = self.pages.index(page)
    bar = self.tabs.tabBar()

    holder = QtGui.QWidget(bar)
    holder.setObjectName("TriggerCloseHolder")
    holder.setFixedSize(22, 20)

    button = PaintedIconButton(
        builtin_icon("close"),
        10,
        parent=holder,
        interactive=True,
        hover_feedback=True
    )
    button.setObjectName("TriggerCloseButton")
    button.setFixedSize(18, 18)
    button.move(2, 1)
    button.setToolTip("Remove trigger")
    button.clicked.connect(
        lambda current=page:
        self.remove_binding(current)
    )

    try:
        bar.setTabButton(
            index,
            QtGui.QTabBar.RightSide,
            holder
        )
    except Exception:
        holder.deleteLater()


def _ensure_add_button(self):
    if self._add_tab_button is not None:
        return

    bar = self.tabs.tabBar()
    button = PaintedIconButton(
        builtin_icon("add"),
        12,
        parent=bar,
        interactive=False,
        hover_feedback=False
    )
    button.setObjectName("TriggerAddButton")
    button.setFixedSize(16, 16)
    button.setToolTip("Add trigger")
    self._add_tab_button = button


def install_icon_clip_fix():
    if getattr(
        TriggerTabBindingPanel,
        _INSTALL_MARKER,
        False
    ):
        return

    # The trigger panel methods are replaced before property editors are
    # instantiated. QTabBar still owns the holder geometry, but QToolButton
    # and QStyle no longer participate in painting the plus/close glyphs.
    TriggerTabBindingPanel._install_trigger_close_button = (
        _install_trigger_close_button
    )
    TriggerTabBindingPanel._ensure_add_button = _ensure_add_button

    setattr(
        TriggerTabBindingPanel,
        _INSTALL_MARKER,
        True
    )


__all__ = [
    "PaintedIconButton",
    "install_icon_clip_fix",
]
