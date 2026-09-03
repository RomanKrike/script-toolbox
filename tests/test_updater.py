# -*- coding: utf-8 -*-

from script_toolbox.core.updater import is_newer_version


def test_stable_release_is_newer_than_same_dev_version():
    assert is_newer_version(
        "0.2.0",
        "0.2.0-dev"
    )


def test_older_release_is_not_newer():
    assert not is_newer_version(
        "0.1.9",
        "0.2.0-dev"
    )


def test_v_prefix_is_supported():
    assert is_newer_version(
        "v1.0.0",
        "0.9.9"
    )


def test_same_version_is_not_newer():
    assert not is_newer_version(
        "1.2.3",
        "1.2.3"
    )
