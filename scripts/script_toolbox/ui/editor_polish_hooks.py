# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
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
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 2px;
}
QToolButton#EditorSearchClear:hover {
    background-color: #404040;
    border-color: #545454;
}
QToolButton#EditorSearchClear:pressed {
    background-color: #272727;
    border-color: #171717;
}
"""

_ICON_ONLY_STYLE = """
QPushButton#ScriptButton {
    text-align: center;
    padding-left: 0px;
    padding-right: 0px;
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


def _search_control(line_edit, parent):
    container = QtGui.QWidget(parent)
    container.setObjectName("EditorSearchControl")
    layout = QtGui.QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)

    search_icon = QtGui.QToolButton(container)
    search_icon.setObjectName("EditorSearchIcon")
    search_icon.setIcon(
        builtin_icon("find")
    )
    search_icon.setIconSize(
        QtCore.QSize(14, 14)
    )
    search_icon.setFixedSize(24, 24)
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

    clear_button = QtGui.QToolButton(container)
    clear_button.setObjectName("EditorSearchClear")
    clear_button.setIcon(
        builtin_icon("close")
    )
    clear_button.setIconSize(
        QtCore.QSize(12, 12)
    )
    clear_button.setFixedSize(24, 24)
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

    def update_clear(value):
        clear_button.setVisible(
            bool(text_type(value or ""))
        )

    line_edit.textChanged.connect(
        update_clear
    )
    update_clear(
        line_edit.text()
    )

    layout.addWidget(search_icon)
    layout.addWidget(line_edit, 1)
    layout.addWidget(clear_button)

    container._script_toolbox_search_icon = search_icon
    container._script_toolbox_clear_button = clear_button
    return container


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


def _install_centered_button_icon(button):
    icon = button.icon()
    if icon.isNull():
        return

    icon_size = button.iconSize()
    if (
        icon_size.width() <= 0 or
        icon_size.height() <= 0
    ):
        icon_size = QtCore.QSize(18, 18)

    # Do not convert QIcon to QPixmap here. Older Qt SVG engines used by Maya
    # can return an empty pixmap before the widget is shown even though the
    # QIcon itself paints correctly. A transparent child QToolButton keeps the
    # original QIcon and lets Qt render it normally at an exact layout center.
    button.setIcon(
        QtGui.QIcon()
    )
    button.setText("")

    layout = QtGui.QHBoxLayout(
        button
    )
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    icon_button = QtGui.QToolButton(
        button
    )
    icon_button.setObjectName(
        "ScriptButtonCenteredIcon"
    )
    icon_button.setAutoRaise(True)
    icon_button.setIcon(icon)
    icon_button.setIconSize(icon_size)
    icon_button.setFixedSize(
        icon_size.width() + 2,
        icon_size.height() + 2
    )
    icon_button.setFocusPolicy(
        QtCore.Qt.NoFocus
    )
    icon_button.setStyleSheet(
        "QToolButton#ScriptButtonCenteredIcon {"
        "background: transparent;"
        "border: 0px;"
        "padding: 0px;"
        "}"
    )
    try:
        icon_button.setAttribute(
            QtCore.Qt.WA_TransparentForMouseEvents,
            True
        )
    except Exception:
        pass

    layout.addStretch(1)
    layout.addWidget(
        icon_button,
        0,
        QtCore.Qt.AlignCenter
    )
    layout.addStretch(1)

    button._script_toolbox_centered_icon = icon_button


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
        button = original(
            owner,
            item,
            compact=compact
        )

        if (
            button is not None and
            bool(item.get("icon_only", False))
        ):
            button.setProperty(
                "iconOnly",
                True
            )
            current_style = text_type(
                button.styleSheet() or ""
            )
            button.setStyleSheet(
                current_style +
                "\n" +
                _ICON_ONLY_STYLE
            )
            _install_centered_button_icon(
                button
            )

        return button

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
            bool(item.get("icon_only", False))
        ):
            widget = self.state_button_widgets.get(
                item.get("id")
            )
            if widget is not None:
                widget.setText("")
                current_style = text_type(
                    widget.styleSheet() or ""
                )
                if "text-align: center;" not in current_style:
                    widget.setStyleSheet(
                        current_style +
                        "\n" +
                        _ICON_ONLY_STYLE
                    )

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
    "IconFeedbackFilter",
    "install_editor_search_ux",
    "install_icon_only_button_centering",
    "install_icon_only_state_refresh",
    "install_runtime_icon_feedback",
]
