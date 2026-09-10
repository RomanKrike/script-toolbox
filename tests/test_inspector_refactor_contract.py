# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _source(*parts):
    path = os.path.join(ROOT, *parts)
    with open(path, "r") as handle:
        return handle.read()


def test_inspector_section_order_and_reusable_contract_are_stable():
    source = _source(
        "scripts", "script_toolbox", "ui", "properties", "sections.py"
    )

    expected = (
        "SECTION_GENERAL",
        "SECTION_LAYOUT",
        "SECTION_CONTAINER_LAYOUT",
        "SECTION_CONTENT",
        "SECTION_APPEARANCE",
        "SECTION_INTERFACE_OPTIONS",
        "SECTION_BEHAVIOR",
        "SECTION_TRIGGERS",
    )
    order_block = source.split("INSPECTOR_SECTION_ORDER = (", 1)[1].split(
        ")", 1
    )[0]
    positions = [order_block.index(name) for name in expected]
    assert positions == sorted(positions)

    assert "class InspectorSection" in source
    assert "self.key =" in source
    assert "self.title =" in source
    assert "collapsedChanged" in source
    assert "self.content" in source
    assert "self.form = QtGui.QFormLayout()" in source
    assert "set_property_available" in source


def test_inspector_and_runtime_compose_one_collapsible_section_primitive():
    sections = _source(
        "scripts", "script_toolbox", "ui", "properties", "sections.py"
    )
    component = _source(
        "scripts", "script_toolbox", "ui", "collapsible_folder.py"
    )
    builtin_icons = _source(
        "scripts", "script_toolbox", "style", "builtin_icons.py"
    )
    ui_source = _source(
        "scripts", "script_toolbox", "ui", "__init__.py"
    )

    # One visual primitive owns all collapse presentation and interaction.
    assert "class CollapsibleSection(QtGui.QFrame):" in component
    assert "collapsedChanged = QtCore.Signal(bool)" in component
    assert 'self.setObjectName("RuntimeFolder")' in component
    assert 'self.setProperty("folderType", "collapsible")' in component
    assert 'self.content.setObjectName("RuntimeFolderContent")' in component
    assert 'self.setProperty("collapsed", collapsed)' in component
    assert 'self.header.setProperty("collapsed", collapsed)' in component
    assert '"right" if self._collapsed else "down"' in component
    assert "def _repolish(self):" in component

    # InspectorSection is only a form adapter; it does not implement chrome.
    assert "class InspectorSection(QtGui.QWidget):" in sections
    assert "self.section = CollapsibleSection(" in sections
    assert "self.header = self.section.header" in sections
    assert "self.content = self.section.content" in sections
    assert "self.section.set_collapsed(" in sections
    assert "configure_collapsible_folder_frame" not in sections
    assert "set_collapsible_folder_state" not in sections
    assert 'u"\\u25b8"' not in sections
    assert 'u"\\u25be"' not in sections

    # RuntimeFolder keeps its class identity and composes the same primitive.
    assert "def install_runtime_folder_composition(runtime_module):" in component
    assert "self.collapsible_section = CollapsibleSection(" in component
    assert "self.collapsible_section.collapsedChanged.connect(" in component
    assert "runtime_class.__init__ = runtime_folder_init" in component
    assert "runtime_module.RuntimeFolder = SharedRuntimeFolder" not in component
    assert "class SharedRuntimeFolder" not in component

    # Persisted state is handled outside CollapsibleSection itself.
    class_block = component.split(
        "class CollapsibleSection(QtGui.QFrame):",
        1
    )[1].split(
        "def install_runtime_folder_composition(runtime_module):",
        1
    )[0]
    assert "toolbox.save" not in class_block
    assert "preferences" not in class_block
    assert "self.toolbox" not in class_block

    assert '("right", "Expand", "alt-arrow-right.svg")' in builtin_icons
    assert "from .collapsible_folder import CollapsibleSection" in ui_source
    assert "from .collapsible_folder import install_runtime_folder_composition" in ui_source
    assert "install_runtime_folder_composition(" in ui_source
    assert "install_runtime_folder_chrome(" not in ui_source


def test_property_editor_base_uses_sections_instead_of_one_shared_form():
    source = _source(
        "scripts", "script_toolbox", "ui", "properties", "base.py"
    )

    assert "self.form =" not in source
    for attribute in (
        "general_section",
        "layout_section",
        "container_layout_section",
        "content_section",
        "appearance_section",
        "interface_options_section",
        "behavior_section",
        "trigger_section",
    ):
        assert attribute in source

    for label in (
        '"Name"',
        '"Label"',
        '"Show Label"',
        '"Tooltip"',
        '"Width Mode"',
        '"Fixed Width"',
        '"Width Stretch"',
        '"Height Mode"',
        '"Fixed Height"',
        '"Height Stretch"',
        '"Horizontal Alignment"',
        '"Vertical Alignment"',
    ):
        assert label in source

    assert "self.binding_panel = BindingPanel" in source
    assert "self.trigger_section.addWidget" in source
    assert 'self.binding_panel.setTitle("Events")' in source


def test_item_editors_route_controls_to_semantic_sections():
    basic = _source(
        "scripts", "script_toolbox", "ui", "properties", "basic.py"
    )
    field = _source(
        "scripts", "script_toolbox", "ui", "properties", "field.py"
    )
    button = _source(
        "scripts", "script_toolbox", "ui", "properties", "button.py"
    )
    toggle_button = _source(
        "scripts", "script_toolbox", "ui", "properties", "toggle_button.py"
    )
    toggle_icon = _source(
        "scripts", "script_toolbox", "ui", "properties", "toggle_icon.py"
    )
    icon = _source(
        "scripts", "script_toolbox", "ui", "properties", "icon.py"
    )

    assert 'self.content_section.addRow("Value", self.value)' in basic
    assert '"Component Labels"' in basic
    assert 'self.appearance_section.addRow("Color", self.button)' in basic
    assert '"Label Position"' in basic

    assert 'self.content_section.addRow("Source", self.source)' in field
    assert 'self.content_section.addRow("Display", self.display_mode)' in field
    assert '"Visible Rows"' in field
    assert '"Selectable"' in field
    assert '"Select Scene on Double Click"' in field
    assert '"Use Full Paths"' in field

    assert "section = self.appearance_section" in button
    assert '"Icon Size"' in button
    assert '"ON Color"' in button
    assert "self.add_trigger_widget(" in button
    assert '"Get State"' in button
    assert '"Turn ON"' in button
    assert '"Turn OFF"' in button

    assert 'self.behavior_section.addRow(' in toggle_button
    assert '"State Source"' in toggle_button
    assert '"Internal State"' in toggle_button
    assert "state_get_script" in button
    assert "state_on_script" in button
    assert "state_off_script" in button

    assert 'self.behavior_section.addRow(' in toggle_icon
    assert "section = self.appearance_section" in toggle_icon
    assert "self.add_trigger_widget(" in toggle_icon
    assert "state_get_script" in toggle_icon
    assert "state_on_script" in toggle_icon
    assert "state_off_script" in toggle_icon

    assert "self.appearance_section.addRow(" in icon
    assert '"Content Alignment"' in icon


def test_universal_applicability_disables_controls_without_schema_changes():
    sections = _source(
        "scripts", "script_toolbox", "ui", "properties", "sections.py"
    )
    adapter = _source(
        "scripts", "script_toolbox", "ui", "properties", "layout_adapter.py"
    )
    basic = _source(
        "scripts", "script_toolbox", "ui", "properties", "basic.py"
    )
    constants = _source(
        "scripts", "script_toolbox", "constants.py"
    )

    assert "widget.setEnabled(available)" in sections
    assert "widget.setToolTip(reason)" in sections
    assert "Controlled by parent Row because Equal Child Size is enabled." in adapter
    assert "Controlled by parent Column > Cross Alignment." in adapter
    assert "self.set_property_available(" in basic
    assert "Separator does not display a label." in basic
    assert "CONFIG_VERSION = 19" in constants

    for forbidden in (
        "expression_language",
        "dependency_graph",
        "system_handlers",
    ):
        assert forbidden not in adapter
        assert forbidden not in sections


def test_property_editors_no_longer_append_to_shared_self_form():
    folder = os.path.join(
        ROOT, "scripts", "script_toolbox", "ui", "properties"
    )
    for filename in os.listdir(folder):
        if not filename.endswith(".py") or filename == "sections.py":
            continue
        source = _source(
            "scripts", "script_toolbox", "ui", "properties", filename
        )
        assert "self.form.addRow" not in source


def test_trigger_sizing_targets_stable_trigger_section():
    source = _source(
        "scripts", "script_toolbox", "ui", "properties", "script_editor_sizing.py"
    )

    assert '"trigger_section"' in source
    assert "self.root_layout.indexOf(" in source
    assert "self.binding_panel" in source
