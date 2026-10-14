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


def token_colors(colors):
    """Retain the existing tonal offsets around each editable semantic color."""
    groups = {
        "window": "WINDOW_BG CONTENT_BG STATUS_BG SCROLL_TRACK_BG",
        "panel": "PANEL_BG PROPERTY_BG STRUCTURE_FOLDER_BG FOLDER_CARD_BG FOLDER_NESTED_BG FOLDER_HEADER_BG FOLDER_HEADER_COLLAPSED_BG FOLDER_NESTED_HEADER_BG FOLDER_NESTED_HEADER_COLLAPSED_BG SIMPLE_SECTION_NESTED_BG",
        "input": "CONTROL_BG LIST_BG INPUT_BG LIST_ALT_BG FILTER_BG TOOLTIP_BG ICON_BUTTON_PRESSED_BG",
        "border": "BORDER_TOPBAR BORDER_DARK BORDER_PRESSED BORDER_INSET BORDER_SOFT BORDER_PANEL BORDER_TAB BORDER_DISABLED BORDER_GROUP SEPARATOR TOOLTIP_BORDER HOVER_BORDER ICON_BUTTON_HOVER_BORDER ICON_BUTTON_HOVER_BG LIST_HOVER_BG FOLDER_HEADER_HOVER_BG FOLDER_HEADER_PRESSED_BG FOLDER_NESTED_HEADER_HOVER_BG TAB_HOVER_BG TAB_SELECTED_BG SCROLL_HANDLE_BG SCROLL_HANDLE_HOVER_BG",
        "text": "TEXT_PRIMARY TEXT_STRONG TEXT_HEADING TEXT_PANE_TITLE TEXT_BUTTON TEXT_INPUT TEXT_LIST TEXT_TAB_SELECTED TEXT_SECTION TEXT_SECTION_NESTED TEXT_FOLDER_NESTED TEXT_FOLDER_HOVER TOOLBAR_ICON",
        "secondary": "TEXT_MUTED TEXT_STATUS TEXT_EDITOR_STATUS TEXT_HEADER TEXT_TAB TEXT_SUBTLE TEXT_DISABLED TEXT_INPUT_DISABLED TEXT_FOLDER_COLLAPSED SCROLL_HANDLE_PRESSED_BG",
        "accent": "ACCENT FOCUS_BORDER INPUT_SELECTION_BG UPDATE_BG UPDATE_BORDER UPDATE_HOVER_BG UPDATE_HOVER_BORDER UPDATE_PRESSED_BG UPDATE_DISABLED_BG UPDATE_DISABLED_TEXT UPDATE_DISABLED_BORDER ACCEPT_BG ACCEPT_BORDER ACCEPT_HOVER_BG ACCEPT_HOVER_BORDER",
        "selection": "SELECTION_BG",
        "button": "BUTTON_BG BUTTON_HOVER_BG BUTTON_PRESSED_BG SCRIPT_BUTTON_BG",
    }
    result = dict(_DEFAULT_PALETTE)
    for role, names in groups.items():
        delta = tuple(a - b for a, b in zip(_rgb(colors[role]), _rgb(themes.DEFAULT_COLORS[role])))
        for name in names.split():
            original = _DEFAULT_PALETTE[name].lower()
            rgb = [max(0, min(255, c + d)) for c, d in zip(_rgb(original), delta)]
            result[name] = "#{0:02x}{1:02x}{2:02x}".format(*rgb)
    direct = {
        "on_accent": "TEXT_ON_ACCENT SELECTION_TEXT",
        "group": "TEXT_PALETTE_GROUP", "row": "TEXT_STRUCTURE_ROW",
        "column": "TEXT_STRUCTURE_COLUMN", "code_gutter": "CODE_GUTTER_BG",
        "code_line": "CODE_CURRENT_LINE_BG", "code_numbers": "CODE_LINE_NUMBER",
        "syntax_keyword": "SYNTAX_KEYWORD", "syntax_string": "SYNTAX_STRING",
        "syntax_comment": "SYNTAX_COMMENT", "syntax_number": "SYNTAX_NUMBER",
        "syntax_host": "SYNTAX_HOST", "expression_error": "EXPRESSION_ERROR",
    }
    for role, names in direct.items():
        for name in names.split():
            result[name] = colors[role]
    result["BORDER_FOLDER_NESTED"] = result["BORDER_GROUP"]
    return result


def color_map(colors):
    # QSS uses the shared UI roles. Named painting roles are resolved separately
    # because equal default hex values can have different semantic meanings.
    values = token_colors(colors)
    excluded = set("CODE_GUTTER_BG CODE_CURRENT_LINE_BG CODE_LINE_NUMBER SYNTAX_KEYWORD SYNTAX_STRING SYNTAX_COMMENT SYNTAX_NUMBER SYNTAX_HOST TEXT_STRUCTURE_COLUMN TEXT_STRUCTURE_ROW TEXT_PALETTE_GROUP EXPRESSION_ERROR".split())
    excluded.update(("BUTTON_BG", "BUTTON_HOVER_BG", "BUTTON_PRESSED_BG", "SCRIPT_BUTTON_BG"))
    return dict((_DEFAULT_PALETTE[name].lower(), value) for name, value in values.items()
                if name not in excluded)


def themed_color(name, owner):
    app = QtGui.QApplication.instance()
    manager = getattr(app, "_script_toolbox_themes", None)
    if manager is not None and manager._owned(owner):
        return manager.colors.get(name, manager.active["colors"].get(name))
    return _DEFAULT_PALETTE.get(name, themes.DEFAULT_COLORS.get(name))


_ITEM_COLORS = QtCore.Qt.UserRole + 187


def set_item_color(item, column, name, background=False):
    """Keep semantic metadata on cells; custom item colors remain untouched."""
    key = "background" if background else "foreground"
    roles = item.data(column, _ITEM_COLORS) or {}
    if hasattr(roles, "toPyObject"):
        roles = roles.toPyObject() or {}
    roles = dict(roles)
    roles[key] = name
    item.setData(column, _ITEM_COLORS, roles)
    owner = item.treeWidget()
    manager = getattr(QtGui.QApplication.instance(), "_script_toolbox_themes", None)
    color = manager.colors[name] if owner is None and manager is not None else themed_color(name, owner)
    brush = QtGui.QBrush(QtGui.QColor(color))
    (item.setBackground if background else item.setForeground)(column, brush)


class ThemeController(QtCore.QObject):
    def __init__(self, app):
        QtCore.QObject.__init__(self, app)
        self.active, unused = themes.load_state()
        self._custom_colors = self.active["colors"] != themes.DEFAULT_COLORS
        self._styled = False
        self.roots = []
        self._busy = False
        self._pending = False
        self.mapping = color_map(self.active["colors"])
        self.colors = token_colors(self.active["colors"])
        app.installEventFilter(self)

    def register(self, root):
        if not any(ref() is root for ref in self.roots):
            self.roots.append(weakref.ref(root))
        self.refresh()

    def apply(self, value):
        self.active = themes.validate(value)
        self._custom_colors = self.active["colors"] != themes.DEFAULT_COLORS
        self.mapping = color_map(self.active["colors"])
        self.colors = token_colors(self.active["colors"])
        self.refresh()

    def _owned(self, widget):
        roots = [ref() for ref in self.roots]
        while widget is not None:
            if widget in roots:
                return True
            widget = widget.parent()
        return False

    def eventFilter(self, watched, event):
        if ((self._custom_colors or self._styled) and not self._busy and not self._pending and
                event.type() in (QtCore.QEvent.ChildAdded, QtCore.QEvent.Show, QtCore.QEvent.StyleChange) and
                isinstance(watched, QtGui.QWidget) and self._owned(watched)):
            self._pending = True
            QtCore.QTimer.singleShot(0, self.refresh)
        return False

    def _transform(self, value):
        styled = _HEX.sub(lambda match: self.mapping.get(match.group(0).lower(), match.group(0)), value)
        # Semantic annotations keep equal hex values independent across controls.
        return re.sub(r"#[0-9a-fA-F]{6}(;\s*/\* toolbox-color:(\w+) \*/)",
                      lambda match: self.colors[match.group(2)] + match.group(1), styled)

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
            result.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(self.active["colors"]["on_accent"]))
            if result != current_palette:
                widget.setPalette(result)
        if widget.property("toolboxThemeSelection"):
            current_palette = QtGui.QWidget.palette(widget)
            result = QtGui.QPalette(current_palette)
            result.setColor(QtGui.QPalette.Highlight, QtGui.QColor(self.colors["SELECTION_BG"]))
            result.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(self.colors["SELECTION_TEXT"]))
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
                    roles = entry.data(column, _ITEM_COLORS) or {}
                    if hasattr(roles, "toPyObject"):
                        roles = roles.toPyObject() or {}
                    for key, name in roles.items():
                        brush = QtGui.QBrush(QtGui.QColor(self.colors[name]))
                        (entry.setBackground if key == "background" else entry.setForeground)(column, brush)
                for index in range(entry.childCount()):
                    visit(entry.child(index))
            for index in range(widget.topLevelItemCount()):
                visit(widget.topLevelItem(index))
        callback = getattr(widget, "toolbox_theme_changed", None)
        if callable(callback) and getattr(widget, "_theme_render_colors", None) != self.active["colors"]:
            widget._theme_render_colors = dict(self.active["colors"])
            callback()
        for highlighter in widget.findChildren(QtGui.QSyntaxHighlighter):
            if getattr(highlighter, "_theme_render_colors", None) != self.active["colors"]:
                highlighter._theme_render_colors = dict(self.active["colors"])
                callback = getattr(highlighter, "toolbox_theme_changed", None)
                if callable(callback):
                    callback()
        widget.update()
        for action in QtGui.QWidget.actions(widget):
            action.setIcon(self._icon(action.icon()))

    def refresh(self):
        self._pending = False
        if self._busy or (not self._custom_colors and not self._styled):
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
            self._styled = self._custom_colors
        finally:
            self._busy = False


def controller():
    app = QtGui.QApplication.instance()
    value = getattr(app, "_script_toolbox_themes", None)
    if value is None:
        value = ThemeController(app)
        app._script_toolbox_themes = value
    return value
