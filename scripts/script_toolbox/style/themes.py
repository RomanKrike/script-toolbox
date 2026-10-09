# -*- coding: utf-8 -*-
"""Apply UI themes only within registered Toolbox windows, including local QSS.

The original styles remain immutable. Rebuilding controls or changing a local
style triggers a scoped refresh, so theme previews do not rebuild item data.
"""
import re
import weakref

from ..compat import QtCore, QtGui
from ..core import themes
from . import palette
from .builtin_icons import themed_icon

_DEFAULT_PALETTE = dict((key, getattr(palette, key)) for key in palette.__all__)
_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


def _rgb(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def color_map(colors):
    """Retain the existing tonal offsets around each editable semantic color."""
    groups = {
        "window": "WINDOW_BG CONTENT_BG STATUS_BG SCROLL_TRACK_BG",
        "panel": "PANEL_BG PROPERTY_BG STRUCTURE_FOLDER_BG FOLDER_CARD_BG FOLDER_NESTED_BG FOLDER_HEADER_BG FOLDER_HEADER_COLLAPSED_BG FOLDER_NESTED_HEADER_BG FOLDER_NESTED_HEADER_COLLAPSED_BG SIMPLE_SECTION_NESTED_BG CODE_CURRENT_LINE_BG",
        "input": "CONTROL_BG LIST_BG INPUT_BG LIST_ALT_BG FILTER_BG TOOLTIP_BG ICON_BUTTON_PRESSED_BG",
        "border": "BORDER_TOPBAR BORDER_DARK BORDER_PRESSED BORDER_INSET BORDER_SOFT BORDER_PANEL BORDER_TAB BORDER_DISABLED BORDER_GROUP SEPARATOR TOOLTIP_BORDER HOVER_BORDER ICON_BUTTON_HOVER_BORDER BUTTON_BG BUTTON_HOVER_BG BUTTON_PRESSED_BG ICON_BUTTON_HOVER_BG LIST_HOVER_BG FOLDER_HEADER_HOVER_BG FOLDER_HEADER_PRESSED_BG FOLDER_NESTED_HEADER_HOVER_BG CODE_GUTTER_BG TAB_HOVER_BG TAB_SELECTED_BG SCROLL_HANDLE_BG SCROLL_HANDLE_HOVER_BG",
        "text": "TEXT_PRIMARY TEXT_STRONG TEXT_HEADING TEXT_PANE_TITLE TEXT_BUTTON TEXT_INPUT TEXT_LIST TEXT_TAB_SELECTED TEXT_SECTION TEXT_SECTION_NESTED TEXT_FOLDER_NESTED TEXT_FOLDER_HOVER TOOLBAR_ICON",
        "secondary": "TEXT_MUTED TEXT_STATUS TEXT_EDITOR_STATUS TEXT_HEADER TEXT_TAB TEXT_SUBTLE TEXT_DISABLED TEXT_INPUT_DISABLED TEXT_FOLDER_COLLAPSED CODE_LINE_NUMBER SCROLL_HANDLE_PRESSED_BG",
        "accent": "ACCENT FOCUS_BORDER INPUT_SELECTION_BG UPDATE_BG UPDATE_BORDER UPDATE_HOVER_BG UPDATE_HOVER_BORDER UPDATE_PRESSED_BG UPDATE_DISABLED_BG UPDATE_DISABLED_TEXT UPDATE_DISABLED_BORDER ACCEPT_BG ACCEPT_BORDER ACCEPT_HOVER_BG ACCEPT_HOVER_BORDER TEXT_PALETTE_GROUP",
        "selection": "SELECTION_BG",
    }
    result = {}
    for role, names in groups.items():
        delta = tuple(a - b for a, b in zip(_rgb(colors[role]), _rgb(themes.DEFAULT_COLORS[role])))
        for name in names.split():
            original = _DEFAULT_PALETTE[name].lower()
            rgb = [max(0, min(255, c + d)) for c, d in zip(_rgb(original), delta)]
            result[original] = "#{0:02x}{1:02x}{2:02x}".format(*rgb)
    return result


class ThemeController(QtCore.QObject):
    def __init__(self, app):
        QtCore.QObject.__init__(self, app)
        self.active, unused = themes.load_state()
        self.roots = []
        self._busy = False
        self._pending = False
        self.mapping = color_map(self.active["colors"])
        app.installEventFilter(self)

    def register(self, root):
        if not any(ref() is root for ref in self.roots):
            self.roots.append(weakref.ref(root))
        self.refresh()

    def apply(self, value):
        self.active = themes.validate(value)
        self.mapping = color_map(self.active["colors"])
        self.refresh()

    def _owned(self, widget):
        roots = [ref() for ref in self.roots]
        while widget is not None:
            if widget in roots:
                return True
            widget = widget.parent()
        return False

    def eventFilter(self, watched, event):
        if (not self._busy and not self._pending and
                event.type() in (QtCore.QEvent.ChildAdded, QtCore.QEvent.Show, QtCore.QEvent.StyleChange) and
                isinstance(watched, QtGui.QWidget) and self._owned(watched)):
            self._pending = True
            QtCore.QTimer.singleShot(0, self.refresh)
        return False

    def _transform(self, value):
        return _HEX.sub(lambda match: self.mapping.get(match.group(0).lower(), match.group(0)), value)

    def _icon(self, icon):
        return themed_icon(icon, self.active["colors"]["text"])

    def _widget(self, widget):
        current = widget.styleSheet()
        previous = getattr(widget, "_theme_last_style", None)
        if current != previous:
            widget._theme_base_style = current
        base = getattr(widget, "_theme_base_style", current)
        styled = self._transform(base)
        widget._theme_last_style = styled
        if current != styled:
            widget.setStyleSheet(styled)
        # Only opted-in Qt4 viewport fallbacks need an explicit palette.
        # Assigning palettes to ordinary children freezes inherited QSS colors.
        surface = widget.property("toolboxThemeSurface")
        if surface in ("content", "input"):
            current_palette = QtGui.QWidget.palette(widget)
            result = QtGui.QPalette(current_palette)
            background = self.active["colors"]["window" if surface == "content" else "input"]
            for role in (QtGui.QPalette.Window, QtGui.QPalette.Base, QtGui.QPalette.AlternateBase):
                result.setColor(role, QtGui.QColor(background))
            result.setColor(QtGui.QPalette.Text, QtGui.QColor(self.active["colors"]["text"]))
            result.setColor(QtGui.QPalette.Highlight, QtGui.QColor(self.active["colors"]["selection"]))
            if result != current_palette:
                widget.setPalette(result)
        if isinstance(widget, QtGui.QAbstractButton):
            widget.setIcon(self._icon(widget.icon()))
        if isinstance(widget, QtGui.QListWidget):
            for index in range(widget.count()):
                entry = widget.item(index)
                entry.setIcon(self._icon(entry.icon()))
        if isinstance(widget, QtGui.QTreeWidget):
            def visit(entry):
                for column in range(widget.columnCount()):
                    entry.setIcon(column, self._icon(entry.icon(column)))
                for index in range(entry.childCount()):
                    visit(entry.child(index))
            for index in range(widget.topLevelItemCount()):
                visit(widget.topLevelItem(index))
        for action in QtGui.QWidget.actions(widget):
            action.setIcon(self._icon(action.icon()))

    def refresh(self):
        self._pending = False
        if self._busy:
            return
        self._busy = True
        live = []
        try:
            for ref in self.roots:
                root = ref()
                if root is None:
                    continue
                try:
                    widgets = [root] + root.findChildren(QtGui.QWidget)
                except RuntimeError:
                    continue
                live.append(ref)
                for widget in widgets:
                    self._widget(widget)
            self.roots = live
        finally:
            self._busy = False


def controller():
    app = QtGui.QApplication.instance()
    value = getattr(app, "_script_toolbox_themes", None)
    if value is None:
        value = ThemeController(app)
        app._script_toolbox_themes = value
    return value
