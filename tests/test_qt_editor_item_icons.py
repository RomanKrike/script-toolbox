"""Item symbols are identical and visible in both editor trees."""
from test_qt_lifecycle import run_qt, pytestmark as qt_mark

pytestmark = qt_mark


def test_item_icons_in_creation_and_existing_trees(tmp_path):
    run_qt('''
from script_toolbox.model import create_item
from script_toolbox.model.item_registry import ITEM_TYPES
from script_toolbox.style.builtin_icons import item_type_icon
from script_toolbox.style.metrics import EDITOR_ITEM_ICON_SIZE
from script_toolbox.ui.item_palette import palette_groups
kinds = [kind for group, entries in palette_groups() for label, kind, tooltip in entries]
w.config['sections'][0]['items'] = [create_item(kind, {'name': 'icon_test_' + kind}) for kind in kinds]
w.rebuild()
w.open_interface_editor()
e = w.editor_window
pump()
assert e.palette.iconSize() == QtCore.QSize(EDITOR_ITEM_ICON_SIZE, EDITOR_ITEM_ICON_SIZE)
assert e.tree.iconSize() == e.palette.iconSize()
found = {}
for i in range(e.palette.topLevelItemCount()):
    group = e.palette.topLevelItem(i)
    for j in range(group.childCount()):
        entry = group.child(j)
        kind = entry.data(0, QtCore.Qt.UserRole)
        assert not entry.icon(0).isNull(), kind
        assert not entry.icon(0).pixmap(16, 16).isNull(), kind
        found[kind] = entry.icon(0).cacheKey()
assert set(found) == set(kinds)
def check(node):
    kind = node.data(0, QtCore.Qt.UserRole)
    assert not node.icon(0).isNull(), kind
    assert node.icon(0).cacheKey() == found[kind], kind
    for index in range(node.childCount()):
        check(node.child(index))
for index in range(e.tree.topLevelItemCount()):
    check(e.tree.topLevelItem(index))
assert not item_type_icon('extension_kind').isNull()
e.close()
w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_settings_category_icons_and_navigation(tmp_path):
    run_qt('''
from script_toolbox.ui.settings_dialog import SettingsDialog
from script_toolbox.style.metrics import SETTINGS_CATEGORY_ICON_SIZE
from script_toolbox.style.builtin_icons import settings_category_icon
d = SettingsDialog(w)
d.resize(900, 600)
d.show()
pump()
keys = ('general', 'network', 'integrations', 'library', 'privacy', 'about')
assert d.category_list.count() == len(keys)
for index, key in enumerate(keys):
    entry = d.category_list.item(index)
    assert not entry.icon().isNull(), key
    assert not entry.icon().pixmap(16, 16).isNull(), key
    assert entry.icon().cacheKey() == settings_category_icon(key).cacheKey(), key
    d.category_list.setCurrentRow(index)
    assert d.pages.currentIndex() == index
assert d.category_list.iconSize() == QtCore.QSize(SETTINGS_CATEGORY_ICON_SIZE, SETTINGS_CATEGORY_ICON_SIZE)
d.reject()
pump()
w.close()
w.deleteLater()
pump()
''', tmp_path)
