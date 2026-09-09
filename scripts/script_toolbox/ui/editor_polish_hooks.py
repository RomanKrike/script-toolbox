# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..pycompat import text_type


_EDITOR_SEARCH_MARKER = "_script_toolbox_editor_search_polish"
_BUTTON_CENTER_MARKER = "_script_toolbox_icon_only_button_centering"

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

_ICON_ONLY_STYLE = """
QPushButton#ScriptButton {
    text-align: center;
    padding-left: 0px;
    padding-right: 0px;
}
"""


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


def _install_search_fields(self):
    palette_layout = None
    palette_parent = None
    try:
        palette_parent = self.palette.parentWidget()
        palette_layout = palette_parent.layout()
    except Exception:
        palette_layout = None

    if palette_layout is not None:
        try:
            # Keep the filter at the bottom of Create Parameters but remove
            # the redundant instructional copy below it. This leaves the
            # search directly under the palette instead of under helper text.
            _hide_palette_hint(
                palette_parent
            )
            palette_layout.removeWidget(
                self.palette_filter
            )
            palette_layout.addWidget(
                self.palette_filter
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
    tree_layout.addWidget(
        self.existing_filter
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

    pixmap = icon.pixmap(
        icon_size
    )
    if pixmap.isNull():
        return

    # QSS text-align does not reliably center QPushButton icons in older
    # Qt/Maya styles. Render the icon as a child label in a symmetric layout
    # so its geometry is centered independently of the host button style.
    button.setIcon(
        QtGui.QIcon()
    )
    button.setText("")

    layout = QtGui.QHBoxLayout(
        button
    )
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    icon_label = QtGui.QLabel(
        button
    )
    icon_label.setObjectName(
        "ScriptButtonCenteredIcon"
    )
    icon_label.setAlignment(
        QtCore.Qt.AlignCenter
    )
    icon_label.setFixedSize(
        icon_size
    )
    icon_label.setPixmap(
        pixmap
    )
    try:
        icon_label.setAttribute(
            QtCore.Qt.WA_TransparentForMouseEvents,
            True
        )
    except Exception:
        pass

    layout.addStretch(1)
    layout.addWidget(
        icon_label,
        0,
        QtCore.Qt.AlignCenter
    )
    layout.addStretch(1)

    button._script_toolbox_centered_icon = icon_label


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


__all__ = [
    "install_editor_search_ux",
    "install_icon_only_button_centering",
]
