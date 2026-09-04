from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError("anchor not found in %s" % path)
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Scroll the property panel instead of letting large editors compress/overflow.
replace(
    "scripts/script_toolbox/ui/interface_editor.py",
    '''        self.property_host = QtGui.QWidget()\n        self.property_layout = QtGui.QVBoxLayout(\n            self.property_host\n        )\n        self.property_layout.setContentsMargins(\n            0,\n            0,\n            0,\n            0\n        )\n        right_layout.addWidget(\n            self.property_host,\n            1\n        )\n''',
    '''        self.property_scroll = QtGui.QScrollArea()\n        self.property_scroll.setObjectName(\n            "PropertyScroll"\n        )\n        self.property_scroll.setWidgetResizable(\n            True\n        )\n        self.property_scroll.setFrameShape(\n            QtGui.QFrame.NoFrame\n        )\n        self.property_scroll.setHorizontalScrollBarPolicy(\n            QtCore.Qt.ScrollBarAlwaysOff\n        )\n\n        self.property_host = QtGui.QWidget()\n        self.property_host.setObjectName(\n            "PropertyHost"\n        )\n        self.property_layout = QtGui.QVBoxLayout(\n            self.property_host\n        )\n        self.property_layout.setContentsMargins(\n            0,\n            0,\n            4,\n            0\n        )\n        self.property_scroll.setWidget(\n            self.property_host\n        )\n        right_layout.addWidget(\n            self.property_scroll,\n            1\n        )\n'''
)

# Do not force folders/rows open while merely normalizing the editor tree.
replace(
    "scripts/script_toolbox/ui/interface_editor.py",
    '''                    normalize_folder(\n                        child\n                    )\n                    child.setExpanded(\n                        True\n                    )\n                    child_index += 1\n''',
    '''                    normalize_folder(\n                        child\n                    )\n                    child_index += 1\n'''
)
replace(
    "scripts/script_toolbox/ui/interface_editor.py",
    '''                    child.setExpanded(\n                        True\n                    )\n                    child_index += 1\n                    continue\n''',
    '''                    child_index += 1\n                    continue\n'''
)

# Duplicate the item that actually opened the context menu, normalize first,
# then restore selection to the clone. This avoids Qt4 current-item jumps.
replace(
    "scripts/script_toolbox/ui/interface_editor.py",
    '''    def duplicate_selected(self):\n        current = self.tree.currentItem()\n        if current is None:\n            return\n\n        self.sync_working_from_tree()\n        item_id = self.item_data(current, ROLE_ID)\n        data = self.item_cache.get(item_id)\n        if data is None:\n            return\n\n        clone = self._clone_data(\n            data,\n            self._used_names()\n        )\n        tree_item = self._insert_cloned_tree_item(\n            clone,\n            sibling=True\n        )\n        self.tree.setCurrentItem(tree_item)\n        self.fix_tree_structure()\n        self.tree_changed()\n''',
    '''    def duplicate_selected(\n        self,\n        target_item=None\n    ):\n        current = target_item or self.tree.currentItem()\n        if current is None:\n            return\n\n        self.tree.setCurrentItem(\n            current\n        )\n        self.sync_working_from_tree()\n        item_id = self.item_data(current, ROLE_ID)\n        data = self.item_cache.get(item_id)\n        if data is None:\n            return\n\n        clone = self._clone_data(\n            data,\n            self._used_names()\n        )\n        tree_item = self._insert_cloned_tree_item(\n            clone,\n            sibling=True\n        )\n\n        try:\n            tree_item.setExpanded(\n                current.isExpanded()\n            )\n        except Exception:\n            pass\n\n        self.fix_tree_structure()\n        self.tree_changed()\n\n        selected = self.tree_item_by_id(\n            text_type(clone["id"])\n        )\n        if selected is None:\n            selected = tree_item\n\n        self.tree.setCurrentItem(\n            selected\n        )\n        try:\n            self.tree.scrollToItem(\n                selected,\n                QtGui.QAbstractItemView.EnsureVisible\n            )\n        except Exception:\n            pass\n'''
)
replace(
    "scripts/script_toolbox/ui/interface_editor.py",
    '''        elif action == duplicate_action:\n            self.duplicate_selected()\n''',
    '''        elif action == duplicate_action:\n            self.duplicate_selected(\n                item\n            )\n'''
)

# Reset the property scroll position whenever a new parameter editor is shown.
replace(
    "scripts/script_toolbox/ui/interface_editor.py",
    '''        self.property_layout.addWidget(\n            editor\n        )\n\n    def property_changed(self):\n''',
    '''        self.property_layout.addWidget(\n            editor\n        )\n        try:\n            self.property_scroll.verticalScrollBar().setValue(\n                0\n            )\n        except Exception:\n            pass\n\n    def property_changed(self):\n'''
)

# Keep the Field description compact; the property panel now scrolls when needed.
replace(
    "scripts/script_toolbox/ui/properties/field.py",
    '''        self.value = QtGui.QPlainTextEdit()\n        self.value.setMinimumHeight(72)\n''',
    '''        self.value = QtGui.QPlainTextEdit()\n        self.value.setMinimumHeight(64)\n        self.value.setMaximumHeight(92)\n'''
)
replace(
    "scripts/script_toolbox/ui/properties/field.py",
    '''        self.form.addRow("Source", self.source)\n        self.form.addRow("Value", self.value)\n        self.form.addRow("Placeholder", self.placeholder)\n        self.form.addRow("Display", self.display_mode)\n        self.form.addRow("Visible Rows", self.visible_rows)\n        self.form.addRow("", self.selectable)\n        self.form.addRow("", self.select_scene)\n        self.form.addRow("", self.multiple)\n        self.form.addRow("", self.long_names)\n''',
    '''        self.form.addRow("Source", self.source)\n        self.form.addRow("Display", self.display_mode)\n        self.form.addRow("Value", self.value)\n        self.form.addRow("Placeholder", self.placeholder)\n        self.form.addRow("", self.multiple)\n        self.form.addRow("Visible Rows", self.visible_rows)\n        self.form.addRow("", self.selectable)\n        self.form.addRow("", self.select_scene)\n        self.form.addRow("", self.long_names)\n'''
)

# Version bump.
replace(
    "scripts/script_toolbox/constants.py",
    'PLUGIN_VERSION = "0.4.0"',
    'PLUGIN_VERSION = "0.4.1"'
)
replace(
    "MayaScriptToolbox.mod",
    "+ MayaScriptToolbox 0.4.0 .",
    "+ MayaScriptToolbox 0.4.1 ."
)

# Changelog entry.
p = Path("CHANGELOG.md")
text = p.read_text(encoding="utf-8")
entry = '''# Changelog\n\n## 0.4.1\n\nInterface Editor regression fix release.\n\n### Fixed\n\n- Make Parameter Description scrollable so Field 2.0 and other large property editors no longer compress or overlap controls.\n- Tighten the Field property layout and keep its manual multi-value editor bounded to a compact height.\n- Preserve folder/row expansion state while normalizing the Existing Parameters tree.\n- Make context-menu Duplicate target the item that opened the menu and keep the duplicated item selected after normalization.\n\n'''
if not text.startswith("# Changelog\n\n"):
    raise RuntimeError("unexpected changelog header")
text = entry + text[len("# Changelog\n\n"):]
p.write_text(text, encoding="utf-8")
