# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..model.items import safe_color
from ..pycompat import text_type
from ..style.builtin_icons import builtin_icon


_EDITOR_SEARCH_MARKER = "_script_toolbox_editor_search_polish"
_BUTTON_CENTER_MARKER = "_script_toolbox_icon_only_button_centering"
_STATE_BUTTON_MARKER = "_script_toolbox_icon_only_state_refresh"
_ICON_FEEDBACK_MARKER = "_script_toolbox_runtime_icon_feedback"

_EXISTING_FILTER_STYLE = """
QLineEdit#ExistingParametersFilter {
    background-color: #262626;
    border: 1px solid #191919;
    border-radius: 2px;
    min-height: 24px;
    padding: 2px 7px;
}
QLineEdit#ExistingParametersFilter:focus {
    border: 1px solid #78604a;
}
"""

_TECH_ICON_STYLE = """
QToolButton#EditorSearchIcon,
QToolButton#EditorSearchClear {
    background-color: transparent;
    border: 0px;
    padding: 0px;
}
QToolButton#EditorSearchClear:hover {
    background-color: #404040;
    border: 0px;
    border-radius: 3px;
}
QToolButton#EditorSearchClear:pressed {
    background-color: #272727;
    border: 0px;
    border-radius: 3px;
}
"""

_ICON_FEEDBACK_BASE = (
    "background-color: transparent;"
    "border: 1px solid transparent;"
    "border-radius: 3px;"
    "padding: 3px;"
)
_ICON_FEEDBACK_HOVER = (
    "background-color: #404040;"
    "border: 1px solid #545454;"
    "border-radius: 3px;"
    "padding: 3px;"
)
_ICON_FEEDBACK_PRESSED = (
    "background-color: #272727;"
    "border: 1px solid #171717;"
    "border-radius: 3px;"
    "padding: 3px;"
)

_SEARCH_ICON_SIZE = 18
_CLEAR_BUTTON_SIZE = 20


def _tree_item_matches(item, query):
    if not query:
        return True

    values = []
    for column in range(3):
        try:
            values.append(
                text_type(item.text(column)).lower()
            )
        except Exception:
            pass

    try:
        values.append(
            text_type(item.toolTip(0)).lower()
        )
    except Exception:
        pass

    return any(
        query in value
        for value in values
    )


def _filter_tree_branch(item, query):
    child_match = False

    for child_index in range(item.childCount()):
        child = item.child(child_index)
        if _filter_tree_branch(child, query):
            child_match = True

    visible = (
        _tree_item_matches(item, query) or
        child_match
    )
    item.setHidden(not visible)

    if query and child_match:
        item.setExpanded(True)

    return visible


def _filter_existing_parameters(self, value):
    query = text_type(
        value or ""
    ).strip().lower()

    for index in range(
        self.tree.topLevelItemCount()
    ):
        _filter_tree_branch(
            self.tree.topLevelItem(index),
            query
        )


def _hide_palette_hint(palette_parent):
    try:
        labels = palette_parent.findChildren(
            QtGui.QLabel
        )
    except Exception:
        labels = []

    for label in labels:
        try:
            if text_type(label.objectName()) == "HintText":
                label.hide()
        except Exception:
            pass


def _position_search_icons(
    line_edit,
    search_icon,
    clear_button
):
    search_top = max(
        0,
        (line_edit.height() - _SEARCH_ICON_SIZE) // 2
    )
    clear_top = max(
        0,
        (line_edit.height() - _CLEAR_BUTTON_SIZE) // 2
    )

    search_icon.move(
        4,
        search_top
    )
    clear_button.move(
        max(
            4,
            line_edit.width() - _CLEAR_BUTTON_SIZE - 5
        ),
        clear_top
    )

    try:
        search_icon.raise_()
        clear_button.raise_()
    except Exception:
        pass


class SearchFieldDecorationFilter(QtCore.QObject):

    def __init__(
        self,
        line_edit,
        search_icon,
        clear_button,
        parent=None
    ):
        QtCore.QObject.__init__(
            self,
            parent
        )
        self.line_edit = line_edit
        self.search_icon = search_icon
        self.clear_button = clear_button

    def eventFilter(self, watched, event):
        if event.type() in (
            QtCore.QEvent.Resize,
            QtCore.QEvent.Show,
        ):
            _position_search_icons(
                self.line_edit,
                self.search_icon,
                self.clear_button
            )
        return False


def _search_control(line_edit, parent=None):
    search_icon = QtGui.QToolButton(
        line_edit
    )
    search_icon.setObjectName(
        "EditorSearchIcon"
    )
    search_icon.setAutoRaise(True)
    search_icon.setIcon(
        builtin_icon("find")
    )
    search_icon.setIconSize(
        QtCore.QSize(12, 12)
    )
    search_icon.setFixedSize(
        _SEARCH_ICON_SIZE,
        _SEARCH_ICON_SIZE
    )
    search_icon.setFocusPolicy(
        QtCore.Qt.NoFocus
    )
    search_icon.setToolTip("Search")
    search_icon.setStyleSheet(
        _TECH_ICON_STYLE
    )
    try:
        search_icon.setAttribute(
            QtCore.Qt.WA_TransparentForMouseEvents,
            True
        )
    except Exception:
        pass

    clear_button = QtGui.QToolButton(
        line_edit
    )
    clear_button.setObjectName(
        "EditorSearchClear"
    )
    clear_button.setAutoRaise(True)
    clear_button.setIcon(
        builtin_icon("close")
    )
    # Keep extra breathing room around the Solar close glyph. Maya/Qt4 can
    # otherwise crop the left antialiased edge at small odd icon sizes.
    clear_button.setIconSize(
        QtCore.QSize(9, 9)
    )
    clear_button.setFixedSize(
        _CLEAR_BUTTON_SIZE,
        _CLEAR_BUTTON_SIZE
    )
    clear_button.setFocusPolicy(
        QtCore.Qt.NoFocus
    )
    clear_button.setToolTip("Clear search")
    clear_button.setStyleSheet(
        _TECH_ICON_STYLE
    )
    clear_button.clicked.connect(
        line_edit.clear
    )

    try:
        line_edit.setTextMargins(
            25,
            0,
            28,
            0
        )
    except Exception:
        pass

    def update_clear(value):
        clear_button.setVisible(
            bool(text_type(value or ""))
        )
        _position_search_icons(
            line_edit,
            search_icon,
            clear_button
        )

    line_edit.textChanged.connect(
        update_clear
    )

    decoration_filter = SearchFieldDecorationFilter(
        line_edit,
        search_icon,
        clear_button,
        parent=line_edit
    )
    line_edit.installEventFilter(
        decoration_filter
    )
    line_edit._script_toolbox_search_icon = search_icon
    line_edit._script_toolbox_clear_button = clear_button
    line_edit._script_toolbox_search_filter = decoration_filter

    update_clear(
        line_edit.text()
    )
    return line_edit


def _install_search_fields(self):
    palette_layout = None
    palette_parent = None
    try:
        palette_parent = self.palette.parentWidget()
        palette_layout = palette_parent.layout()
    except Exception:
        palette_layout = None

    if (
        palette_layout is not None and
        not hasattr(self, "palette_search_control")
    ):
        try:
            _hide_palette_hint(
                palette_parent
            )
            palette_layout.removeWidget(
                self.palette_filter
            )
            self.palette_search_control = _search_control(
                self.palette_filter,
                palette_parent
            )
            palette_layout.addWidget(
                self.palette_search_control
            )
        except Exception:
            pass

    if hasattr(self, "existing_filter"):
        return

    try:
        tree_parent = self.tree.parentWidget()
        tree_layout = tree_parent.layout()
    except Exception:
        tree_parent = None
        tree_layout = None

    if tree_layout is None:
        return

    self.existing_filter = QtGui.QLineEdit(
        tree_parent
    )
    self.existing_filter.setObjectName(
        "ExistingParametersFilter"
    )
    try:
        self.existing_filter.setPlaceholderText(
            "Filter existing parameters..."
        )
    except Exception:
        pass
    self.existing_filter.setStyleSheet(
        _EXISTING_FILTER_STYLE
    )
    self.existing_filter.textChanged.connect(
        self.filter_existing_parameters
    )
    self.existing_search_control = _search_control(
        self.existing_filter,
        tree_parent
    )
    tree_layout.addWidget(
        self.existing_search_control
    )


def install_editor_search_ux(editor_class):
    if getattr(
        editor_class,
        _EDITOR_SEARCH_MARKER,
        False
    ):
        return

    original_build_ui = editor_class.build_ui
    original_populate_tree = editor_class.populate_tree

    def build_ui(self):
        original_build_ui(self)
        _install_search_fields(self)

    def populate_tree(self):
        original_populate_tree(self)
        search = getattr(
            self,
            "existing_filter",
            None
        )
        if search is not None:
            self.filter_existing_parameters(
                search.text()
            )

    editor_class.filter_existing_parameters = (
        _filter_existing_parameters
    )
    editor_class.build_ui = build_ui
    editor_class.populate_tree = populate_tree
    setattr(
        editor_class,
        _EDITOR_SEARCH_MARKER,
        True
    )


class CenteredIconPushButton(QtGui.QPushButton):
    """QPushButton that paints its icon at the exact widget center."""

    def __init__(self, parent=None):
        QtGui.QPushButton.__init__(
            self,
            "",
            parent
        )
        self._centered_icon = QtGui.QIcon()
        self._centered_icon_size = QtCore.QSize(18, 18)

    def setCenteredIcon(self, icon, size):
        self._centered_icon = QtGui.QIcon(icon)
        self._centered_icon_size = QtCore.QSize(size)
        QtGui.QPushButton.setIcon(
            self,
            QtGui.QIcon()
        )
        QtGui.QPushButton.setText(
            self,
            ""
        )
        self.update()

    def setText(self, value):
        QtGui.QPushButton.setText(
            self,
            ""
        )

    def paintEvent(self, event):
        QtGui.QPushButton.paintEvent(
            self,
            event
        )

        if self._centered_icon.isNull():
            return

        width = max(
            1,
            self._centered_icon_size.width()
        )
        height = max(
            1,
            self._centered_icon_size.height()
        )
        target = QtCore.QRect(
            (self.width() - width) // 2,
            (self.height() - height) // 2,
            width,
            height
        )

        mode = (
            QtGui.QIcon.Disabled
            if not self.isEnabled()
            else QtGui.QIcon.Active
            if self.underMouse()
            else QtGui.QIcon.Normal
        )
        state = (
            QtGui.QIcon.On
            if self.isDown()
            else QtGui.QIcon.Off
        )

        painter = QtGui.QPainter(self)
        try:
            self._centered_icon.paint(
                painter,
                target,
                QtCore.Qt.AlignCenter,
                mode,
                state
            )
        except TypeError:
            self._centered_icon.paint(
                painter,
                target
            )
        painter.end()


def _button_should_center_icon(item):
    icon_path = text_type(
        item.get("icon_path") or ""
    ).strip()
    if not icon_path:
        return False

    if bool(item.get("icon_only", False)):
        return True

    # The common editor workflow is to assign an icon and disable Show Label.
    # In that case the native QPushButton still keeps its icon at the left.
    if not bool(item.get("show_label", True)):
        return True

    return not bool(
        text_type(item.get("label") or "").strip()
    )


def _render_centered_icon_button(
    owner,
    item
):
    state_mode = item.get(
        "mode",
        "action"
    ) == "state"

    button = CenteredIconPushButton()
    button.setObjectName(
        "ScriptButton"
    )
    try:
        button.setToolTip(
            owner._tooltip(item)
        )
    except Exception:
        button.setToolTip(
            item.get("tooltip", "")
        )

    color = (
        item.get("state_off_color")
        if state_mode
        else item.get("color")
    )
    rgb = [
        int(value * 255)
        for value in safe_color(color)
    ]
    button.setStyleSheet(
        "QPushButton#ScriptButton {"
        "background-color: rgb(%d,%d,%d);"
        "}" % (
            rgb[0],
            rgb[1],
            rgb[2]
        )
    )

    icon_path = os.path.expanduser(
        os.path.expandvars(
            text_type(
                item.get("icon_path") or ""
            )
        )
    )
    icon_size = int(
        item.get("icon_size", 18)
    )
    if icon_path:
        button.setCenteredIcon(
            QtGui.QIcon(icon_path),
            QtCore.QSize(
                icon_size,
                icon_size
            )
        )

    button.clicked.connect(
        lambda checked=False, item_id=item["id"]:
        owner.toolbox.run_item(item_id)
    )

    if state_mode:
        owner.toolbox.register_state_button(
            item["id"],
            button
        )

    return button


def install_icon_only_button_centering(registry):
    if getattr(
        registry,
        _BUTTON_CENTER_MARKER,
        False
    ):
        return

    original = registry.renderer_for("button")
    if original is None:
        return

    def render_button(owner, item, compact=False):
        if _button_should_center_icon(item):
            return _render_centered_icon_button(
                owner,
                item
            )

        return original(
            owner,
            item,
            compact=compact
        )

    registry.register(
        "button",
        render_button,
        replace=True
    )
    setattr(
        registry,
        _BUTTON_CENTER_MARKER,
        True
    )


def install_icon_only_state_refresh(main_window_class):
    if getattr(
        main_window_class,
        _STATE_BUTTON_MARKER,
        False
    ):
        return

    original = main_window_class.refresh_state_button

    def refresh_state_button(self, key):
        result = original(self, key)
        item = self.find_item(key)

        if (
            item is not None and
            item.get("kind") == "button" and
            _button_should_center_icon(item)
        ):
            widget = self.state_button_widgets.get(
                item.get("id")
            )
            if widget is not None:
                widget.setText("")

        return result

    main_window_class.refresh_state_button = refresh_state_button
    setattr(
        main_window_class,
        _STATE_BUTTON_MARKER,
        True
    )


class IconFeedbackFilter(QtCore.QObject):

    def __init__(self, target, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.target = target

    def _set_style(self, style):
        try:
            self.target.setStyleSheet(style)
        except Exception:
            pass

    def eventFilter(self, watched, event):
        event_type = event.type()

        if event_type == QtCore.QEvent.Enter:
            self._set_style(
                _ICON_FEEDBACK_HOVER
            )
        elif event_type == QtCore.QEvent.Leave:
            self._set_style(
                _ICON_FEEDBACK_BASE
            )
        elif event_type == QtCore.QEvent.MouseButtonPress:
            self._set_style(
                _ICON_FEEDBACK_PRESSED
            )
        elif event_type == QtCore.QEvent.MouseButtonRelease:
            self._set_style(
                _ICON_FEEDBACK_HOVER
            )

        return False


def _runtime_icon_target(widget):
    candidates = []
    try:
        candidates = widget.findChildren(
            QtGui.QWidget
        )
    except Exception:
        pass

    for candidate in candidates:
        if isinstance(
            candidate,
            (QtGui.QAbstractButton, QtGui.QLabel)
        ):
            return candidate

    return None


def install_runtime_icon_feedback(registry):
    if getattr(
        registry,
        _ICON_FEEDBACK_MARKER,
        False
    ):
        return

    original = registry.renderer_for("icon")
    if original is None:
        return

    def render_icon(owner, item, compact=False):
        widget = original(
            owner,
            item,
            compact=compact
        )
        if widget is None:
            return widget

        target = _runtime_icon_target(
            widget
        )
        if target is None:
            return widget

        try:
            target.setObjectName(
                "RuntimeIconFeedback"
            )
            current_size = target.size()
            if (
                current_size.width() > 0 and
                current_size.height() > 0
            ):
                target.setFixedSize(
                    current_size.width() + 6,
                    current_size.height() + 6
                )
            target.setStyleSheet(
                _ICON_FEEDBACK_BASE
            )
            feedback_filter = IconFeedbackFilter(
                target,
                parent=target
            )
            target.installEventFilter(
                feedback_filter
            )
            target._script_toolbox_icon_feedback = feedback_filter
        except Exception:
            pass

        return widget

    registry.register(
        "icon",
        render_icon,
        replace=True
    )
    setattr(
        registry,
        _ICON_FEEDBACK_MARKER,
        True
    )


__all__ = [
    "CenteredIconPushButton",
    "IconFeedbackFilter",
    "SearchFieldDecorationFilter",
    "install_editor_search_ux",
    "install_icon_only_button_centering",
    "install_icon_only_state_refresh",
    "install_runtime_icon_feedback",
]
