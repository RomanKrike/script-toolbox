import pytest

from script_toolbox.integrations import managed_files, maya

BEGIN = '# begin toolbox'
END = '# end toolbox'
BLOCK = BEGIN + '\nmanaged()\n' + END


def test_duplicate_blocks_keep_surrounding_user_code(tmp_path):
    path = tmp_path / 'startup.py'
    path.write_text('before()\n' + BLOCK + '\ninside_user()\n' + BLOCK + '\nafter()\n')
    managed_files.write_marked_block(str(path), BEGIN, END, BLOCK)
    content = path.read_text()
    assert content.count(BEGIN) == 1
    assert content == 'before()\ninside_user()\nafter()\n\n' + BLOCK + '\n'
    assert (tmp_path / 'startup.py.script_toolbox.bak').read_text().count(BEGIN) == 2
    managed_files.remove_marked_block(str(path), BEGIN, END)
    assert path.read_text() == 'before()\ninside_user()\nafter()\n'


@pytest.mark.parametrize('content', [BEGIN + '\nuser()', END + '\nuser()',
                                    END + '\n' + BEGIN, BEGIN + '\n' + BLOCK + '\n' + END])
def test_malformed_blocks_refuse_to_modify_file(tmp_path, content):
    path = tmp_path / 'startup.py'
    path.write_text(content)
    assert managed_files.marked_block_state(str(path), BEGIN, END, BLOCK) == 'broken'
    assert not managed_files.contains_marked_block(str(path), BEGIN, END)
    with pytest.raises(managed_files.ManagedBlockError):
        managed_files.write_marked_block(str(path), BEGIN, END, BLOCK)
    with pytest.raises(managed_files.ManagedBlockError):
        managed_files.remove_marked_block(str(path), BEGIN, END)
    assert path.read_text() == content
    assert not (tmp_path / 'startup.py.script_toolbox.bak').exists()


def test_maya_uses_same_marker_rules():
    block = maya._managed_block()
    assert maya._replace_marked_block(block + '\n' + block, block) == block + '\n'
    with pytest.raises(managed_files.ManagedBlockError):
        maya._replace_marked_block(maya._USER_SETUP_BEGIN + '\nuser()')


def test_atomic_write_failure_preserves_file(tmp_path, monkeypatch):
    path = tmp_path / 'startup.py'
    path.write_text('old')
    def fail(*args):
        raise OSError('disk full')
    monkeypatch.setattr(managed_files, 'replace_file', fail)
    with pytest.raises(OSError):
        managed_files.atomic_write(str(path), 'new')
    assert path.read_text() == 'old'
    assert list(tmp_path.iterdir()) == [path]


def test_maya_malformed_startup_is_reported_and_preserved(tmp_path):
    adapter = maya.MayaAdapter(config_path=str(tmp_path / 'settings.json'))
    setup = tmp_path / 'userSetup.py'
    setup.write_text(maya._USER_SETUP_BEGIN + '\nuser()')
    adapter._user_setup_path = lambda installation: str(setup)
    adapter._shelf_path = lambda installation: str(tmp_path / 'missing_shelf')
    target = maya.DccInstallation(dcc='maya', display_name='Maya', version='2025', user_config_path=str(tmp_path))
    assert adapter.status(target).state == maya.STATUS_BROKEN
    with pytest.raises(managed_files.ManagedBlockError):
        adapter._set_startup_block(target, False)
    assert setup.read_text() == maya._USER_SETUP_BEGIN + '\nuser()'
