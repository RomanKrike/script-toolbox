from script_toolbox.core.restart_ack import acknowledge_restart
from script_toolbox.core import updater


def test_restart_ack_is_written_atomically_and_token_consumed(tmp_path, monkeypatch):
    monkeypatch.setenv('SCRIPT_TOOLBOX_RESTART_TOKEN', 'a' * 32)
    monkeypatch.setattr(updater, 'repository_root', lambda: str(tmp_path))
    assert acknowledge_restart()
    assert (tmp_path / '.script_toolbox_restart_ack').read_text() == 'a' * 32
    assert not (tmp_path / '.script_toolbox_restart_ack.tmp').exists()
    assert not acknowledge_restart()


def test_invalid_restart_token_does_not_write_file(tmp_path, monkeypatch):
    monkeypatch.setenv('SCRIPT_TOOLBOX_RESTART_TOKEN', '../unexpected')
    monkeypatch.setattr(updater, 'repository_root', lambda: str(tmp_path))
    assert not acknowledge_restart()
    assert not list(tmp_path.iterdir())
