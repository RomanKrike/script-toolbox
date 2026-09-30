# -*- coding: utf-8 -*-
"""Acknowledge native portable startup only after its main window is shown."""
import os
import re


def acknowledge_restart():
    token = os.environ.pop('SCRIPT_TOOLBOX_RESTART_TOKEN', '')
    if not re.match(r'^[0-9a-f]{32}$', token):
        return False
    from .updater import repository_root
    path = os.path.join(repository_root(), '.script_toolbox_restart_ack')
    from .config import _replace_file
    temporary = path + '.tmp'
    try:
        with open(temporary, 'wb') as handle:
            handle.write(token.encode('ascii'))
            handle.flush()
            os.fsync(handle.fileno())
        _replace_file(temporary, path)
        return True
    except Exception:
        from .logging_utils import get_logger
        get_logger().exception('Could not acknowledge portable restart.')
        return False
