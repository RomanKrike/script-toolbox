# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..model.items import create_item
from ..model.items import safe_color
from ..pycompat import text_type


class DisplayField(QtGui.QLineEdit):

    def __init__(
        self,
        toolbox,
        item,
        parent=None
    ):
        QtGui.QLineEdit.__init__(
            self,
            parent
        )

        self.toolbox = toolbox
        self.item_id = item["id"]
        self.selectable = bool(
            item.get(
                "selectable",
                True
            )
        )
        self.select_scene = bool(
            item.get(
                "select_scene",
                False
            )
        )

        self.setReadOnly(
            True
        )

        try:
            self.setPlaceholderText(
                item.get(
                    "placeholder",
                    ""
                )
            )
        except Exception:
            pass

        if not self.selectable:
            self.setFocusPolicy(
                QtCore.Qt.NoFocus
            )

        self.setToolTip(
            item.get(
                "tooltip",
                ""
            )
        )

        self.refresh()

    def refresh(self):
        self.setText(
            self.toolbox.field_display_text(
                self.item_id
            )
        )

        if not self.selectable:
            self.deselect()

    def mousePressEvent(self, event):
        if self.selectable:
            QtGui.QLineEdit.mousePressEvent(
                self,
                event
            )
        else:
            event.accept()

    def mouseMoveEvent(self, event):
        if self.selectable:
            QtGui.QLineEdit.mouseMoveEvent(
                self,
                event
            )
        else:
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if self.select_scene:
            self.toolbox.select_field_objects(
                self.item_id
            )

        if self.selectable:
            QtGui.QLineEdit.mouseDoubleClickEvent(
                self,
                event
            )
        else:
            event.accept()


# ----------------------------------------------------------------------
# Runtime interface
# ----------------------------------------------------------------------

class RuntimeFolder(QtGui.QFrame):
    """
    Runtime Folder renderer.

    Internal class name is kept for compatibility with older versions.
    """

    def __init__(
        self,
        toolbox,
        section,
        parent=None,
        embedded=False
    ):
        QtGui.QFrame.__init__(
            self,
            parent
        )
        self.setObjectName(
            "RuntimeFolder"
        )

        self.toolbox = toolbox
        self.section = section
        self.embedded = bool(
            embedded
        )
        self.folder_type = section.get(
            "folder_type",
            "collapsible"
        )

        self.is_nested = False

        try:
            self.is_nested = (
                parent is not None and
                parent.objectName() == "RuntimeFolderContent"
            )
        except Exception:
            self.is_nested = False

        self.setProperty(
            "folderType",
            self.folder_type
        )
        self.setProperty(
            "nested",
            self.is_nested
        )

        root = QtGui.QVBoxLayout(
            self
        )

        if self.folder_type == "collapsible":
            root.setContentsMargins(
                0,
                0,
                0,
                0
            )
            root.setSpacing(
                0
            )
        else:
            root.setContentsMargins(
                0,
                0,
                0,
                4
            )
            root.setSpacing(
                3
            )

        self.arrow = None
        self.header = None
        self.header_button = None
        self.header_label = ""

        # Tabs / Radio pages are embedded and do not draw another header.
        if not self.embedded:
            label = (
                section.get(
                    "label",
                    section["name"]
                )
                if section.get(
                    "show_label",
                    True
                )
                else ""
            )

            if self.folder_type == "collapsible":
                # The full header remains clickable, but the disclosure
                # marker is text instead of the host-native QToolButton arrow.
                # Maya 2015 renders the native arrow disproportionately large.
                self.header_label = text_type(
                    label
                )

                self.header_button = QtGui.QToolButton()
                self.header_button.setObjectName(
                    "RuntimeFolderHeader"
                )
                self.header_button.setToolButtonStyle(
                    QtCore.Qt.ToolButtonTextOnly
                )
                self.header_button.setSizePolicy(
                    QtGui.QSizePolicy.Expanding,
                    QtGui.QSizePolicy.Preferred
                )
                self.header_button.setFocusPolicy(
                    QtCore.Qt.NoFocus
                )
                self.header_button.setToolTip(
                    section.get(
                        "tooltip",
                        ""
                    )
                )
                self.header_button.clicked.connect(
                    self.toggle
                )

                self.arrow = self.header_button

                root.addWidget(
                    self.header_button
                )

            else:
                self.header = QtGui.QFrame()
                self.header.setObjectName(
                    "SimpleSectionHeader"
                )

                header_layout = QtGui.QHBoxLayout(
                    self.header
                )
                header_layout.setContentsMargins(
                    5,
                    2,
                    5,
                    2
                )
                header_layout.setSpacing(
                    4
                )

                title = QtGui.QLabel(
                    label
                )
                title.setObjectName(
                    "SectionTitle"
                )

                header_layout.addWidget(
                    title
                )
                header_layout.addStretch(
                    1
                )

                root.addWidget(
                    self.header
                )

        self.content = QtGui.QWidget()
        self.content.setObjectName(
            "RuntimeFolderContent"
        )
        self.content_layout = QtGui.QVBoxLayout(
            self.content
        )
        if self.folder_type == "collapsible":
            self.content_layout.setContentsMargins(
                9,
                6,
                7,
                7
            )
        else:
            self.content_layout.setContentsMargins(
                9,
                4,
                5,
                3
            )
        self.content_layout.setSpacing(
            3
        )

        self._populate_runtime_items(
            section["items"]
        )

        root.addWidget(
            self.content
        )

        self.update_state()

    def _populate_runtime_items(
        self,
        items
    ):
        """
        Populate this Folder recursively.

        Consecutive nested folders of type Tabs or Radio Buttons are grouped
        inside their current parent Folder, just like at the top level.
        """
        index = 0

        while index < len(
            items
        ):
            item = items[
                index
            ]

            if item.get(
                "kind"
            ) == "folder":
                folder_type = item.get(
                    "folder_type",
                    "collapsible"
                )

                if folder_type in (
                    "tabs",
                    "radio"
                ):
                    group = [
                        item
                    ]
                    index += 1

                    while index < len(
                        items
                    ):
                        candidate = items[
                            index
                        ]

                        if (
                            candidate.get(
                                "kind"
                            ) != "folder" or
                            candidate.get(
                                "folder_type",
                                "collapsible"
                            ) != folder_type
                        ):
                            break

                        group.append(
                            candidate
                        )
                        index += 1

                    if folder_type == "tabs":
                        widget = RuntimeFolderTabs(
                            self.toolbox,
                            group,
                            self.content
                        )
                    else:
                        widget = RuntimeFolderRadio(
                            self.toolbox,
                            group,
                            self.content
                        )

                else:
                    widget = RuntimeFolder(
                        self.toolbox,
                        item,
                        self.content
                    )
                    index += 1

            else:
                widget = self.build_runtime_widget(
                    item,
                    compact=False
                )
                index += 1

            if widget is not None:
                self.content_layout.addWidget(
                    widget
                )


    # ------------------------------------------------------------------
    # Runtime controls
    # ------------------------------------------------------------------

    def _label(self, item):
        if not item.get(
            "show_label",
            True
        ):
            return ""

        return item.get(
            "label",
            item.get(
                "name",
                ""
            )
        )

    def _tooltip(self, item):
        return item.get(
            "tooltip",
            ""
        )

    def _parameter_container(
        self,
        item,
        compact=False
    ):
        widget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout(
            widget
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )
        layout.setSpacing(4)

        label_text = self._label(
            item
        )

        if label_text:
            label = QtGui.QLabel(
                label_text
            )

            if not compact:
                label.setMinimumWidth(
                    105
                )

            layout.addWidget(
                label
            )

        widget.setToolTip(
            self._tooltip(
                item
            )
        )

        return widget, layout

    def _button_widget(
        self,
        item
    ):
        button = QtGui.QPushButton(
            self._label(
                item
            )
        )
        button.setObjectName(
            "ScriptButton"
        )
        button.setToolTip(
            self._tooltip(
                item
            )
        )

        rgb = [
            int(value * 255)
            for value in item.get(
                "color",
                [0.25, 0.25, 0.25]
            )
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

        button.clicked.connect(
            lambda checked=False, item_id=item["id"]:
            self.toolbox.run_item(
                item_id
            )
        )

        return button

    def _toggle_widget(
        self,
        item,
        compact=False
    ):
        container, layout = self._parameter_container(
            item,
            compact=compact
        )

        checkbox = QtGui.QCheckBox()

        checkbox.setToolTip(
            self._tooltip(
                item
            )
        )

        checkbox.setChecked(
            bool(
                item.get(
                    "value",
                    False
                )
            )
        )

        checkbox.toggled.connect(
            lambda value, item_id=item["id"]:
            self.toolbox.store_value(
                item_id,
                bool(value)
            )
        )

        layout.addWidget(
            checkbox,
            0
        )

        return container

    def _checkbox_widget(
        self,
        item,
        compact=False
    ):
        label_position = item.get(
            "label_position",
            "right"
        )

        if label_position == "left":
            container, layout = self._parameter_container(
                item,
                compact=compact
            )

            checkbox = QtGui.QCheckBox()
            checkbox.setToolTip(
                self._tooltip(
                    item
                )
            )
            checkbox.setChecked(
                bool(
                    item.get(
                        "value",
                        False
                    )
                )
            )
            checkbox.toggled.connect(
                lambda value, item_id=item["id"]:
                self.toolbox.store_value(
                    item_id,
                    bool(value)
                )
            )

            layout.addWidget(
                checkbox,
                0
            )

            return container

        checkbox = QtGui.QCheckBox(
            self._label(
                item
            )
        )

        checkbox.setToolTip(
            self._tooltip(
                item
            )
        )

        checkbox.setChecked(
            bool(
                item.get(
                    "value",
                    False
                )
            )
        )

        checkbox.toggled.connect(
            lambda value, item_id=item["id"]:
            self.toolbox.store_value(
                item_id,
                bool(value)
            )
        )

        return checkbox

    def _color_button_style(
        self,
        button,
        color
    ):
        rgb = [
            int(value * 255)
            for value in safe_color(
                color
            )
        ]

        button.setStyleSheet(
            "QPushButton {"
            "background-color: rgb(%d,%d,%d);"
            "}" % (
                rgb[0],
                rgb[1],
                rgb[2]
            )
        )

    def _choose_runtime_color(
        self,
        item_id,
        button
    ):
        value = self.toolbox.get_value(
            item_id,
            [0.5, 0.5, 0.5]
        )

        color = safe_color(
            value
        )

        initial = QtGui.QColor(
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255)
        )

        chosen = QtGui.QColorDialog.getColor(
            initial,
            self,
            "Choose Color"
        )

        if not chosen.isValid():
            return

        value = [
            chosen.red() / 255.0,
            chosen.green() / 255.0,
            chosen.blue() / 255.0
        ]

        self.toolbox.store_value(
            item_id,
            value
        )

        self._color_button_style(
            button,
            value
        )

    def _parameter_widget(
        self,
        item,
        compact=False
    ):
        kind = item.get(
            "kind"
        )

        container, layout = self._parameter_container(
            item,
            compact=compact
        )

        if kind == "string":
            control = QtGui.QLineEdit(
                text_type(
                    item.get(
                        "value",
                        ""
                    )
                )
            )

            if compact:
                control.setMinimumWidth(
                    80
                )

            control.editingFinished.connect(
                lambda item_id=item["id"], widget=control:
                self.toolbox.store_value(
                    item_id,
                    text_type(
                        widget.text()
                    )
                )
            )

        elif kind == "integer":
            control = QtGui.QSpinBox()
            control.setRange(
                item["min"],
                item["max"]
            )
            control.setSingleStep(
                item["step"]
            )
            control.setValue(
                item["value"]
            )

            control.valueChanged.connect(
                lambda value, item_id=item["id"]:
                self.toolbox.store_value(
                    item_id,
                    int(value)
                )
            )

        elif kind == "float":
            control = QtGui.QDoubleSpinBox()
            control.setDecimals(
                item["decimals"]
            )
            control.setRange(
                item["min"],
                item["max"]
            )
            control.setSingleStep(
                item["step"]
            )
            control.setValue(
                item["value"]
            )

            control.valueChanged.connect(
                lambda value, item_id=item["id"]:
                self.toolbox.store_value(
                    item_id,
                    float(value)
                )
            )

        elif kind == "menu":
            control = QtGui.QComboBox()
            control.addItems(
                item["items"]
            )

            index = control.findText(
                item["value"]
            )

            if index >= 0:
                control.setCurrentIndex(
                    index
                )

            control.currentIndexChanged.connect(
                lambda index, item_id=item["id"], widget=control:
                self.toolbox.store_value(
                    item_id,
                    text_type(
                        widget.itemText(
                            index
                        )
                    )
                )
            )

        elif kind == "color":
            control = QtGui.QPushButton(                "..."
                if compact
                else "Choose..."
            )

            self._color_button_style(
                control,
                item["value"]
            )

            control.clicked.connect(
                lambda checked=False, item_id=item["id"], widget=control:
                self._choose_runtime_color(
                    item_id,
                    widget
                )
            )

        else:
            return None

        layout.addWidget(
            control,
            1 if kind in (
                "string",
                "menu"
            ) else 0
        )

        return container

    def _row_widget(
        self,
        item
    ):
        row_widget = QtGui.QWidget()
        row_widget.setToolTip(
            self._tooltip(
                item
            )
        )

        layout = QtGui.QHBoxLayout(
            row_widget
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )
        layout.setSpacing(
            int(
                item.get(
                    "spacing",
                    4
                )
            )
        )

        for child in item.get(
            "items",
            []
        ):
            child_widget = self.build_runtime_widget(
                child,
                compact=True
            )

            if child_widget is not None:
                layout.addWidget(
                    child_widget
                )

        layout.addStretch(
            1
        )

        return row_widget

    def build_runtime_widget(
        self,
        item,
        compact=False
    ):
        kind = item.get(
            "kind"
        )

        if kind == "folder":
            # Normally folders are grouped in _populate_runtime_items().
            # This fallback is useful for direct rendering paths.
            return RuntimeFolder(
                self.toolbox,
                item,
                self.content
            )

        if kind == "row":
            return self._row_widget(
                item
            )

        if kind == "button":
            return self._button_widget(
                item
            )

        if kind == "toggle":
            legacy = create_item("toggle", item)
            return self._checkbox_widget(
                legacy,
                compact=compact
            )

        if kind == "checkbox":
            return self._checkbox_widget(
                item,
                compact=compact
            )

        if kind == "field":
            container, layout = self._parameter_container(
                item,
                compact=compact
            )

            control = DisplayField(
                self.toolbox,
                item,
                container
            )

            if compact:
                control.setMinimumWidth(
                    100
                )

            layout.addWidget(
                control,
                1
            )

            self.toolbox.register_field_widget(
                item["id"],
                control
            )

            return container

        if kind == "label":
            label = QtGui.QLabel(
                self._label(
                    item
                )
            )
            label.setToolTip(
                self._tooltip(
                    item
                )
            )
            label.setStyleSheet(
                "color:#bdbdbd; padding:2px 3px;"
            )
            return label

        if kind == "separator":
            line = QtGui.QFrame()

            line.setFrameShape(
                QtGui.QFrame.VLine
                if compact
                else QtGui.QFrame.HLine
            )
            line.setFrameShadow(
                QtGui.QFrame.Sunken
            )

            return line

        if kind in (
            "string",
            "integer",
            "float",
            "menu",
            "color"
        ):
            return self._parameter_widget(
                item,
                compact=compact
            )

        return None

    # ------------------------------------------------------------------
    # Folder behavior
    # ------------------------------------------------------------------

    def toggle(self):
        if self.folder_type != "collapsible":
            return

        self.section["collapsed"] = not bool(
            self.section.get(
                "collapsed",
                False
            )
        )

        self.toolbox.save()
        self.update_state()

    def update_state(self):
        if (
            self.embedded or
            self.folder_type != "collapsible"
        ):
            self.content.setVisible(
                True
            )
            return

        collapsed = bool(
            self.section.get(
                "collapsed",
                False
            )
        )

        self.content.setVisible(
            not collapsed
        )

        self.setProperty(
            "collapsed",
            collapsed
        )

        if self.header_button is not None:
            marker = (
                u"\u25b8"
                if collapsed
                else u"\u25be"
            )

            self.header_button.setText(
                u"{0}  {1}".format(
                    marker,
                    self.header_label
                )
            )

            self.header_button.setProperty(
                "collapsed",
                collapsed
            )

            # Re-polish so Qt4/Qt5 style sheets immediately see dynamic
            # properties on both the card and its header.
            try:
                self.style().unpolish(
                    self
                )
                self.style().polish(
                    self
                )

                self.header_button.style().unpolish(
                    self.header_button
                )
                self.header_button.style().polish(
                    self.header_button
                )
            except Exception:
                pass


class RuntimeFolderTabs(QtGui.QFrame):

    def __init__(
        self,
        toolbox,
        folders,
        parent=None
    ):
        QtGui.QFrame.__init__(
            self,
            parent
        )

        layout = QtGui.QVBoxLayout(
            self
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            4
        )
        layout.setSpacing(
            0
        )

        self.tabs = QtGui.QTabWidget()
        layout.addWidget(
            self.tabs
        )

        for folder in folders:
            page = RuntimeFolder(
                toolbox,
                folder,
                self.tabs,
                embedded=True
            )

            label = (
                folder.get(
                    "label",
                    folder["name"]
                )
                if folder.get(
                    "show_label",
                    True
                )
                else ""
            )

            self.tabs.addTab(
                page,
                label
            )


class RuntimeFolderRadio(QtGui.QFrame):

    def __init__(
        self,
        toolbox,
        folders,
        parent=None
    ):
        QtGui.QFrame.__init__(
            self,
            parent
        )

        root = QtGui.QVBoxLayout(
            self
        )
        root.setContentsMargins(
            0,
            0,
            0,
            4
        )
        root.setSpacing(
            4
        )

        radio_row = QtGui.QHBoxLayout()
        radio_row.setContentsMargins(
            4,
            2,
            4,
            0
        )
        radio_row.setSpacing(
            8
        )

        self.group = QtGui.QButtonGroup(
            self
        )
        self.stack = QtGui.QStackedWidget()

        for index, folder in enumerate(
            folders
        ):
            label = (
                folder.get(
                    "label",
                    folder["name"]
                )
                if folder.get(
                    "show_label",
                    True
                )
                else ""
            )

            button = QtGui.QRadioButton(
                label
            )

            self.group.addButton(
                button,
                index
            )
            radio_row.addWidget(
                button
            )

            page = RuntimeFolder(
                toolbox,
                folder,
                self.stack,
                embedded=True
            )
            self.stack.addWidget(
                page
            )

            button.toggled.connect(
                lambda checked, i=index:
                self._set_page(
                    checked,
                    i
                )
            )

            if index == 0:
                button.setChecked(
                    True
                )

        radio_row.addStretch(
            1
        )

        root.addLayout(
            radio_row
        )
        root.addWidget(
            self.stack
        )

    def _set_page(
        self,
        checked,
        index
    ):
        if checked:
            self.stack.setCurrentIndex(
                index
            )

def build_folder_widgets(toolbox, folders, parent=None):
    """Build top-level runtime folder widgets with tab/radio grouping."""
    widgets = []
    index = 0

    while index < len(folders):
        folder = folders[index]
        folder_type = folder.get("folder_type", "collapsible")

        if folder_type in ("tabs", "radio"):
            group = [folder]
            index += 1

            while index < len(folders):
                candidate = folders[index]

                if candidate.get("folder_type", "collapsible") != folder_type:
                    break

                group.append(candidate)
                index += 1

            if folder_type == "tabs":
                widget = RuntimeFolderTabs(toolbox, group, parent)
            else:
                widget = RuntimeFolderRadio(toolbox, group, parent)
        else:
            widget = RuntimeFolder(toolbox, folder, parent)
            index += 1

        widgets.append(widget)

    return widgets


# Temporary compatibility alias while the refactor is in progress.
RuntimeSection = RuntimeFolder


__all__ = [
    "DisplayField",
    "RuntimeFolder",
    "RuntimeFolderTabs",
    "RuntimeFolderRadio",
    "RuntimeSection",
    "build_folder_widgets",
]
