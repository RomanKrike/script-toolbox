from test_qt_lifecycle import run_qt, pytestmark as qt_mark

pytestmark = qt_mark


def test_palette_copy_drop_insertion_history_and_rejection(tmp_path):
    run_qt('''
from script_toolbox.model.items import create_item, normalize_document
from script_toolbox.ui.palette_drag import (PALETTE_MIME, palette_source,
    source_data, drop_location, insert_palette_drop)
folder = create_item('folder', {'name': 'tools', 'items': [
    create_item('button', {'name': 'first'}), create_item('row', {'name': 'row'})]})
w.config = normalize_document({'sections': [folder]})
w.open_interface_editor()
e = w.editor_window
e.show()
pump()
root = e.tree.topLevelItem(0)
leaf, row = root.child(0), root.child(1)
assert e.palette.dragEnabled() and e.preset_palette.dragEnabled()
assert palette_source(e, e.palette.topLevelItem(0)) is None
button_palette = None
for i in range(e.palette.topLevelItemCount()):
    group = e.palette.topLevelItem(i)
    for j in range(group.childCount()):
        if e.palette_item_kind(group.child(j)) == 'button':
            button_palette = group.child(j)
assert button_palette is not None
mime = e.palette.mimeData([button_palette])
assert mime.hasFormat(PALETTE_MIME)
assert e.palette.supportedDropActions() == QtCore.Qt.CopyAction
before = e.document_controller.snapshot()
assert drop_location(e.tree, leaf, QtGui.QAbstractItemView.OnItem, 'button') is None
assert drop_location(e.tree, row, QtGui.QAbstractItemView.OnItem, 'folder') is None
assert drop_location(e.tree, None, QtGui.QAbstractItemView.OnViewport, 'button') is None
assert drop_location(e.tree, row, QtGui.QAbstractItemView.OnItem, 'button') == (row, 0)
location = drop_location(e.tree, leaf, QtGui.QAbstractItemView.BelowItem, 'button')
created = e._call_tree_action('Create Parameter', insert_palette_drop,
    {'kind': 'button'}, *location)
new_id = e.item_data(created, QtCore.Qt.UserRole + 1)
assert root.child(1) is created and created.parent() is root
assert e.palette.mimeData([button_palette]).hasFormat(PALETTE_MIME)
assert new_id in e.item_cache
assert w.config['sections'][0]['items'] == folder['items']
e.undo()
assert e.document_controller.snapshot() == before
e.redo()
assert new_id in e.item_cache
# Repeat creation must keep unique names and IDs.
root = e.tree.topLevelItem(0)
second = e._call_tree_action('Create Parameter', insert_palette_drop,
    {'kind': 'button'}, root, 0)
assert e.item_data(second, QtCore.Qt.UserRole + 1) != new_id
assert len(e._used_names()) == len(e.item_cache)
# Managed presets are editable copies when dragged, with rewritten references.
e.preset_resolver.packages['sample'] = {'presets': [{'id': 'example', 'root': folder}]}
source = source_data(e, {'library': ['sample', 'example']})
copy_item = e._call_tree_action('Insert Preset', insert_palette_drop,
    {'library': ['sample', 'example']}, None, e.tree.topLevelItemCount())
copy_id = e.item_data(copy_item, QtCore.Qt.UserRole + 1)
assert copy_id != folder['id'] and source['id'] == folder['id']
assert e.item_cache[copy_id]['items'][0]['kind'] == 'button'
# Actual Qt drag-enter/move/drop events use the same copy path.
class Enter(QtGui.QDragEnterEvent):
    def source(self): return e.palette
class Move(QtGui.QDragMoveEvent):
    def source(self): return e.palette
class Drop(QtGui.QDropEvent):
    def source(self): return e.palette
root.setExpanded(True)
pump()
point = e.tree.visualItemRect(root).center()
enter = Enter(point, QtCore.Qt.CopyAction, mime, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
e.tree.dragEnterEvent(enter)
move = Move(point, QtCore.Qt.CopyAction, mime, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
e.tree.dragMoveEvent(move)
assert move.isAccepted()
count = root.childCount()
drop = Drop(QtCore.QPointF(point), QtCore.Qt.CopyAction, mime, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
e.tree.dropEvent(drop)
assert drop.isAccepted() and root.childCount() == count + 1
assert e.tree.autoExpandDelay() == 700
e.reject()
w.close()
w.deleteLater()
pump()
''', tmp_path)
