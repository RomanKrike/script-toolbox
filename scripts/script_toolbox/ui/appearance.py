# -*- coding: utf-8 -*-
"""Settings appearance editor with a single current-theme selector."""
import copy

from ..compat import QtCore, QtGui
from ..core import themes
from ..pycompat import text_type
from ..style import metrics
from ..style.themes import controller
from .color_control import ColorControl
from .settings_components import build_page_header, build_simple_section, configure_settings_scroll_area


class AppearancePage(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.manager = controller()
        self.original = copy.deepcopy(self.manager.active)
        self.current = copy.deepcopy(self.original)
        unused, self.saved = themes.load_state()
        self._updating = False
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(*metrics.SETTINGS_PAGE_MARGINS)
        layout.setSpacing(metrics.SETTINGS_PAGE_SPACING)
        layout.addWidget(build_page_header("Appearance", "Choose a theme or customize the interface colors.", self))
        theme_row = QtGui.QHBoxLayout()
        theme_row.setSpacing(metrics.SETTINGS_ACTION_SPACING)
        self.theme_combo = QtGui.QComboBox(self)
        self.theme_combo.setObjectName("AppearanceTheme")
        self.theme_combo.setAccessibleName("Theme")
        self.theme_combo.setMinimumWidth(metrics.COLOR_HEX_MIN_WIDTH)
        theme_row.addWidget(self.theme_combo, 1)
        self.actions = QtGui.QWidget(self)
        actions = QtGui.QHBoxLayout(self.actions)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(4)
        self.add_theme_button = QtGui.QPushButton("+", self.actions)
        self.remove_theme_button = QtGui.QPushButton("-", self.actions)
        for button, label, handler in (
                (self.add_theme_button, "Save theme copy", self.save_copy),
                (self.remove_theme_button, "Delete selected user theme", self.remove_theme)):
            button.setFixedSize(metrics.ICON_BUTTON_HEADER_SIZE, metrics.ICON_BUTTON_HEADER_SIZE)
            button.setAutoDefault(False)
            button.setToolTip(label)
            button.setAccessibleName(label)
            button.clicked.connect(handler)
            actions.addWidget(button)
        for label, handler in (("Import", self.import_theme), ("Export", self.export_theme), ("Reset", self.reset_theme)):
            button = QtGui.QPushButton(label, self.actions)
            if label == "Reset":
                button.setToolTip("Restore the default Charcoal palette")
            button.setAutoDefault(False)
            button.clicked.connect(handler)
            actions.addWidget(button)
        theme_row.addWidget(self.actions)
        self.theme_section, theme_layout = build_simple_section("Theme", parent=self)
        theme_layout.addLayout(theme_row)
        layout.addWidget(self.theme_section)
        scroll = QtGui.QScrollArea(self)
        content = QtGui.QWidget(scroll)
        content.setObjectName("SettingsScrollContent")
        sections = QtGui.QVBoxLayout(content)
        sections.setContentsMargins(*metrics.MARGINS_NONE)
        sections.setSpacing(metrics.SETTINGS_SECTION_SPACING)
        self.colors_section, colors_layout = build_simple_section("Interface colors", parent=content)
        sections.addWidget(self.colors_section)
        self.controls = {}
        form = QtGui.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(metrics.SETTINGS_SECTION_SPACING)
        form.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        roles = [role for role in themes.ROLES if role[0] != "button"]
        roles.insert(3, next(role for role in themes.ROLES if role[0] == "button"))
        for key, label, unused in roles:
            control = ColorControl(parent=self.colors_section)
            control.configure(show_rgb=False, show_hex=True)
            control.setFixedWidth(metrics.APPEARANCE_COLOR_FIELD_WIDTH)
            control.setObjectName("AppearanceColor_" + key)
            control.hex_edit.setAccessibleName(label)
            control.valueChanged.connect(lambda value, role=key: self._color_changed(role, value))
            label_widget = QtGui.QLabel(label, self.colors_section)
            label_widget.setBuddy(control.hex_edit)
            field = QtGui.QHBoxLayout()
            field.setContentsMargins(0, 0, 0, 0)
            field.addStretch(1)
            field.addWidget(control)
            form.addRow(label_widget, field)
            self.controls[key] = control
        colors_layout.addLayout(form)
        sections.addStretch(1)
        scroll.setWidget(content)
        configure_settings_scroll_area(scroll)
        layout.addWidget(scroll, 1)
        self.theme_combo.currentIndexChanged.connect(self._selected)
        self._sync()

    def _sync(self):
        self._updating = True
        try:
            self.choices = themes.builtins() + copy.deepcopy(self.saved)
            if not any(value == self.current for value in self.choices):
                self.choices.append(copy.deepcopy(self.current))
            self.theme_combo.clear()
            for value in self.choices:
                self.theme_combo.addItem(value["name"])
            self.theme_combo.setCurrentIndex(self.choices.index(self.current))
            self.remove_theme_button.setEnabled(self.current in self.saved)
            for key, control in self.controls.items():
                color = QtGui.QColor(self.current["colors"][key])
                control.set_value([color.redF(), color.greenF(), color.blueF()])
        finally:
            self._updating = False

    def _selected(self, index):
        if not self._updating and 0 <= index < len(self.choices):
            self.current = copy.deepcopy(self.choices[index])
            self._sync()
            self.manager.apply(self.current)

    def _color_changed(self, role, value):
        if self._updating:
            return
        color = "#{0:02x}{1:02x}{2:02x}".format(*[int(round(c * 255)) for c in value])
        if self.current["colors"][role] == color:
            return
        self.current["name"] = "Custom"
        self.current["colors"][role] = color
        self._sync()
        self.manager.apply(self.current)

    def save_copy(self):
        suggestion = "My Theme" if self.current["name"] == "Custom" else self.current["name"] + " Copy"
        name, accepted = QtGui.QInputDialog.getText(
            self, "Save theme copy", "Theme name:", QtGui.QLineEdit.Normal, suggestion[:80])
        if not accepted:
            return
        name = text_type(name).strip()
        if not name or len(name) > 80:
            self._error("Theme name must contain 1 to 80 characters.")
            return
        value = copy.deepcopy(self.current)
        value["name"] = self._unique_name(name)
        self.saved.append(copy.deepcopy(value))
        self.current = value
        self._sync()
        self.manager.apply(self.current)

    def remove_theme(self):
        if self.current not in self.saved:
            return
        self.saved.remove(self.current)
        self.current = themes.theme()
        self._sync()
        self.manager.apply(self.current)

    def reset_theme(self):
        self.current = themes.theme()
        self._sync()
        self.manager.apply(self.current)

    def _error(self, error):
        QtGui.QMessageBox.warning(self, "Appearance", text_type(error))

    @staticmethod
    def _path(value):
        return value[0] if isinstance(value, tuple) else value

    def _unique_name(self, name):
        taken = set(value["name"] for value in themes.builtins() + self.saved) | set(["Custom"])
        original = name
        index = 2
        while name in taken:
            suffix = " ({0})".format(index)
            name = original[:80 - len(suffix)] + suffix
            index += 1
        return name

    def import_theme(self):
        path = self._path(QtGui.QFileDialog.getOpenFileName(self, "Import theme", "", "UI themes (*.json)"))
        if not path:
            return
        try:
            value = themes.read_theme(path)
            value["name"] = self._unique_name(value["name"])
            self.saved.append(copy.deepcopy(value))
            self.current = value
            self._sync()
            self.manager.apply(self.current)
        except (ValueError, IOError, OSError) as error:
            self._error(error)

    def export_theme(self):
        path = self._path(QtGui.QFileDialog.getSaveFileName(self, "Export theme", self.current["name"] + ".json", "UI themes (*.json)"))
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            themes.write_theme(path, self.current)
        except (ValueError, IOError, OSError) as error:
            self._error(error)

    def save(self):
        current = copy.deepcopy(self.current)
        saved = copy.deepcopy(self.saved)
        try:
            themes.save_state(current, saved)
        except (ValueError, IOError, OSError) as error:
            self._error(error)
            return False
        self.current, self.saved = current, saved
        self.original = copy.deepcopy(current)
        self.manager.apply(current)
        self._sync()
        return True

    def rollback(self):
        self.manager.apply(self.original)
