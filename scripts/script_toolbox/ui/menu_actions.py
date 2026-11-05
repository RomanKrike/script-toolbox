# -*- coding: utf-8 -*-
"""Build menu actions with signatures supported by all host Qt bindings."""
from __future__ import print_function

from ..compat import QtGui


def add_menu_action(menu, text):
    action = QtGui.QAction(text, menu)
    menu.addAction(action)
    return action
