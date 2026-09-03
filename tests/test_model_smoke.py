# -*- coding: utf-8 -*-

# These tests are intentionally Maya-free once the compatibility imports are
# injectable. For now this file documents the first regression targets.

def test_targets():
    assert [
        "legacy toggle -> checkbox/left",
        "nested folders",
        "row rejects nested layout containers",
        "name/label migration",
        "config round-trip",
    ]
