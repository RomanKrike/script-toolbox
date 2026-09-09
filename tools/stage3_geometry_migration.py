from pathlib import Path


def load(path):
    return Path(path).read_text(encoding="utf-8")


def save(path, text):
    Path(path).write_text(text, encoding="utf-8")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit("%s: expected 1 match, got %s" % (label, count))
    return text.replace(old, new, 1)


metrics_path = "scripts/script_toolbox/style/metrics.py"
text = load(metrics_path)
block = '''# Application/editor layout geometry -----------------------------------------
EDITOR_ROOT_MARGINS = (8, 8, 8, 8)
EDITOR_ROOT_SPACING = 7
EDITOR_SPLITTER_HANDLE_WIDTH = 2
EDITOR_PANE_MARGINS = (8, 8, 8, 8)
EDITOR_PANE_SPACING = 6
EDITOR_PROPERTY_HOST_MARGINS = (0, 0, 4, 0)
EDITOR_PALETTE_INDENT = 14
EDITOR_TREE_INDENT = 18
EDITOR_BOTTOM_SPACING = 6
EDITOR_BOTTOM_GROUP_SPACING = 4
EDITOR_ACTION_BUTTON_MIN_WIDTH = 78

TOOLBAR_SPACING = 2
TOOLBAR_GROUP_SPACING = 4

TOOLBOX_TOPBAR_MARGINS = (6, 4, 6, 4)
TOOLBOX_TOPBAR_SPACING = 4
TOOLBOX_CONTENT_MARGINS = (6, 6, 6, 6)
TOOLBOX_CONTENT_SPACING = 5

SCRIPT_EDITOR_ROOT_SPACING = 4
SCRIPT_EDITOR_STATUS_SPACING = 4

SHARE_ACTION_SPACING = 6

'''
text = replace_once(
    text,
    "# Property editor -----------------------------------------------------------\n",
    block + "# Property editor -----------------------------------------------------------\n",
    "metrics application block",
)
exports = '''    "EDITOR_ROOT_MARGINS",
    "EDITOR_ROOT_SPACING",
    "EDITOR_SPLITTER_HANDLE_WIDTH",
    "EDITOR_PANE_MARGINS",
    "EDITOR_PANE_SPACING",
    "EDITOR_PROPERTY_HOST_MARGINS",
    "EDITOR_PALETTE_INDENT",
    "EDITOR_TREE_INDENT",
    "EDITOR_BOTTOM_SPACING",
    "EDITOR_BOTTOM_GROUP_SPACING",
    "EDITOR_ACTION_BUTTON_MIN_WIDTH",
    "TOOLBAR_SPACING",
    "TOOLBAR_GROUP_SPACING",
    "TOOLBOX_TOPBAR_MARGINS",
    "TOOLBOX_TOPBAR_SPACING",
    "TOOLBOX_CONTENT_MARGINS",
    "TOOLBOX_CONTENT_SPACING",
    "SCRIPT_EDITOR_ROOT_SPACING",
    "SCRIPT_EDITOR_STATUS_SPACING",
    "SHARE_ACTION_SPACING",
'''
text = replace_once(
    text,
    '    "PROPERTY_EDITOR_SPACING",\n',
    exports + '    "PROPERTY_EDITOR_SPACING",\n',
    "metrics exports",
)
save(metrics_path, text)

helpers_path = "scripts/script_toolbox/ui/layout_helpers.py"
text = load(helpers_path)
text = replace_once(
    text,
    "def _set_form_growth(form):\n",
    '''def set_layout_margins(layout, margins):
    """Apply shared margins without changing a layout's spacing."""
    _set_contents_margins(
        layout,
        margins
    )
    return layout


def _set_form_growth(form):
''',
    "layout helper function",
)
text = replace_once(
    text,
    '    "configure_property_group_form",\n',
    '    "configure_property_group_form",\n    "set_layout_margins",\n',
    "layout helper export",
)
save(helpers_path, text)

interface_path = "scripts/script_toolbox/ui/interface_editor.py"
text = load(interface_path)
text = replace_once(
    text,
    "from ..style import STYLE\n",
    "from ..style import STYLE\nfrom ..style import metrics\n",
    "interface metrics import",
)
text = replace_once(
    text,
    "from .interface_tree import ExistingInterfaceTree\n",
    "from .interface_tree import ExistingInterfaceTree\nfrom .layout_helpers import configure_layout\nfrom .layout_helpers import set_layout_margins\n",
    "interface helpers import",
)
text = replace_once(
    text,
    '''        root.setContentsMargins(
            8,
            8,
            8,
            8
        )
        root.setSpacing(
            7
        )
''',
    '''        configure_layout(
            root,
            margins=metrics.EDITOR_ROOT_MARGINS,
            spacing=metrics.EDITOR_ROOT_SPACING
        )
''',
    "interface root",
)
text = replace_once(
    text,
    '''        splitter.setHandleWidth(
            2
        )
''',
    '''        splitter.setHandleWidth(
            metrics.EDITOR_SPLITTER_HANDLE_WIDTH
        )
''',
    "interface splitter",
)
pane_old = '''        {name}_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )
        {name}_layout.setSpacing(
            6
        )
'''
pane_new = '''        configure_layout(
            {name}_layout,
            margins=metrics.EDITOR_PANE_MARGINS,
            spacing=metrics.EDITOR_PANE_SPACING
        )
'''
for name in ("left", "center", "right"):
    text = replace_once(
        text,
        pane_old.format(name=name),
        pane_new.format(name=name),
        "interface %s pane" % name,
    )
text = replace_once(
    text,
    '''        self.palette.setIndentation(
            14
        )
''',
    '''        self.palette.setIndentation(
            metrics.EDITOR_PALETTE_INDENT
        )
''',
    "palette indent",
)
text = replace_once(
    text,
    '''        toolbar.setSpacing(
            2
        )
''',
    '''        toolbar.setSpacing(
            metrics.TOOLBAR_SPACING
        )
''',
    "interface toolbar spacing",
)
text = replace_once(
    text,
    '''        self.tree.setIndentation(
            18
        )
''',
    '''        self.tree.setIndentation(
            metrics.EDITOR_TREE_INDENT
        )
''',
    "tree indent",
)
text = replace_once(
    text,
    '''        self.property_layout.setContentsMargins(
            0,
            0,
            4,
            0
        )
''',
    '''        set_layout_margins(
            self.property_layout,
            metrics.EDITOR_PROPERTY_HOST_MARGINS
        )
''',
    "property host margins",
)
text = replace_once(
    text,
    '''        bottom.setSpacing(
            6
        )
''',
    '''        bottom.setSpacing(
            metrics.EDITOR_BOTTOM_SPACING
        )
''',
    "editor bottom spacing",
)
text = replace_once(
    text,
    '''        bottom.addSpacing(
            4
        )
''',
    '''        bottom.addSpacing(
            metrics.EDITOR_BOTTOM_GROUP_SPACING
        )
''',
    "editor bottom group spacing",
)
for label in ("apply_button", "accept_button", "cancel_button"):
    text = replace_once(
        text,
        '''        {0}.setMinimumWidth(
            78
        )
'''.format(label),
        '''        {0}.setMinimumWidth(
            metrics.EDITOR_ACTION_BUTTON_MIN_WIDTH
        )
'''.format(label),
        "editor %s width" % label,
    )
save(interface_path, text)

main_path = "scripts/script_toolbox/ui/main_window.py"
text = load(main_path)
text = replace_once(
    text,
    "from ..style import STYLE\n",
    "from ..style import STYLE\nfrom ..style import metrics\n",
    "main metrics import",
)
text = replace_once(
    text,
    "from .icon_button import create_icon_button\n",
    "from .icon_button import create_icon_button\nfrom .layout_helpers import configure_layout\n",
    "main helper import",
)
text = replace_once(
    text,
    '''        root.setContentsMargins(
            0,
            0,
            0,
            0
        )
        root.setSpacing(
            0
        )
''',
    '''        configure_layout(
            root,
            margins=metrics.MARGINS_NONE,
            spacing=0
        )
''',
    "main root",
)
text = replace_once(
    text,
    '''        top_layout.setContentsMargins(
            6,
            4,
            6,
            4
        )
        top_layout.setSpacing(
            4
        )
''',
    '''        configure_layout(
            top_layout,
            margins=metrics.TOOLBOX_TOPBAR_MARGINS,
            spacing=metrics.TOOLBOX_TOPBAR_SPACING
        )
''',
    "main topbar",
)
text = replace_once(
    text,
    '''        self.content_layout.setContentsMargins(
            6,
            6,
            6,
            6
        )
        self.content_layout.setSpacing(
            5
        )
''',
    '''        configure_layout(
            self.content_layout,
            margins=metrics.TOOLBOX_CONTENT_MARGINS,
            spacing=metrics.TOOLBOX_CONTENT_SPACING
        )
''',
    "main content",
)
save(main_path, text)

script_path = "scripts/script_toolbox/ui/script_editor.py"
text = load(script_path)
text = replace_once(
    text,
    "from ..pycompat import text_type\n",
    "from ..pycompat import text_type\nfrom ..style import metrics\n",
    "script metrics import",
)
text = replace_once(
    text,
    "from .icon_button import create_icon_button\n",
    "from .icon_button import create_icon_button\nfrom .layout_helpers import configure_layout\n",
    "script helper import",
)
text = replace_once(
    text,
    '''        root.setContentsMargins(
            0,
            0,
            0,
            0
        )
        root.setSpacing(
            4
        )
''',
    '''        configure_layout(
            root,
            margins=metrics.MARGINS_NONE,
            spacing=metrics.SCRIPT_EDITOR_ROOT_SPACING
        )
''',
    "script root",
)
text = replace_once(
    text,
    '''        toolbar.setSpacing(
            2
        )
''',
    '''        toolbar.setSpacing(
            metrics.TOOLBAR_SPACING
        )
''',
    "script toolbar spacing",
)
old = '''        toolbar.addSpacing(
            4
        )
'''
new = '''        toolbar.addSpacing(
            metrics.TOOLBAR_GROUP_SPACING
        )
'''
count = text.count(old)
if count != 4:
    raise SystemExit("script toolbar groups: expected 4 matches, got %s" % count)
text = text.replace(old, new)
text = replace_once(
    text,
    '''        status_row.setSpacing(
            4
        )
''',
    '''        status_row.setSpacing(
            metrics.SCRIPT_EDITOR_STATUS_SPACING
        )
''',
    "script status spacing",
)
save(script_path, text)

share_path = "scripts/script_toolbox/ui/share_hooks.py"
text = load(share_path)
text = replace_once(
    text,
    "from ..share import share_data\n",
    "from ..share import share_data\nfrom ..style import metrics\n",
    "share metrics import",
)
text = replace_once(
    text,
    "from .icon_button import create_icon_button\n",
    "from .icon_button import create_icon_button\nfrom .layout_helpers import configure_layout\n",
    "share helper import",
)
text = replace_once(
    text,
    "        layout.setContentsMargins(0, 0, 0, 0)\n        layout.setSpacing(6)\n",
    '''        configure_layout(
            layout,
            margins=metrics.MARGINS_NONE,
            spacing=metrics.SHARE_ACTION_SPACING
        )
''',
    "share action layout",
)
save(share_path, text)

test_path = "tests/test_ui_metrics_contract.py"
text = load(test_path)
addition = r'''


def test_application_layout_geometry_uses_shared_metrics():
    metrics = _read(
        "scripts/script_toolbox/style/metrics.py"
    )
    helpers = _read(
        "scripts/script_toolbox/ui/layout_helpers.py"
    )
    interface = _read(
        "scripts/script_toolbox/ui/interface_editor.py"
    )
    main_window = _read(
        "scripts/script_toolbox/ui/main_window.py"
    )
    script_editor = _read(
        "scripts/script_toolbox/ui/script_editor.py"
    )
    share = _read(
        "scripts/script_toolbox/ui/share_hooks.py"
    )

    for definition in (
        "EDITOR_ROOT_MARGINS = (8, 8, 8, 8)",
        "EDITOR_ROOT_SPACING = 7",
        "EDITOR_PANE_MARGINS = (8, 8, 8, 8)",
        "EDITOR_PANE_SPACING = 6",
        "EDITOR_PALETTE_INDENT = 14",
        "EDITOR_TREE_INDENT = 18",
        "EDITOR_ACTION_BUTTON_MIN_WIDTH = 78",
        "TOOLBAR_SPACING = 2",
        "TOOLBAR_GROUP_SPACING = 4",
        "TOOLBOX_TOPBAR_MARGINS = (6, 4, 6, 4)",
        "TOOLBOX_CONTENT_MARGINS = (6, 6, 6, 6)",
        "SCRIPT_EDITOR_ROOT_SPACING = 4",
        "SHARE_ACTION_SPACING = 6",
    ):
        assert definition in metrics

    assert "def set_layout_margins(layout, margins):" in helpers
    assert "metrics.EDITOR_ROOT_MARGINS" in interface
    assert interface.count("metrics.EDITOR_PANE_MARGINS") == 3
    assert "metrics.EDITOR_ACTION_BUTTON_MIN_WIDTH" in interface
    assert "metrics.TOOLBOX_TOPBAR_MARGINS" in main_window
    assert "metrics.TOOLBOX_CONTENT_MARGINS" in main_window
    assert "metrics.SCRIPT_EDITOR_ROOT_SPACING" in script_editor
    assert script_editor.count("metrics.TOOLBAR_GROUP_SPACING") == 4
    assert "metrics.SHARE_ACTION_SPACING" in share

    assert "setMinimumWidth(\n            78" not in interface
    assert "layout.setSpacing(6)" not in share
'''
if "def test_application_layout_geometry_uses_shared_metrics():" in text:
    raise SystemExit("stage 3 metrics test already exists")
save(test_path, text.rstrip() + addition + "\n")
