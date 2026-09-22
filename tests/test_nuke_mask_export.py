# -*- coding: utf-8 -*-

from script_toolbox.nuke_mask_export import find_channels


class _Node(object):
    def __init__(self, channels):
        self._channels = list(channels)

    def channels(self):
        return list(self._channels)


def test_find_channels_filters_other_mask_prop_passes_and_naturally_sorts():
    node = _Node([
        "rgba.red",
        "other.depth",
        "other.Mask_prop_10_01",
        "other.Mask_prop_02_01",
        "other.Mask_prop_01_03",
        "other.Mask_prop_01_01",
        "Mask_prop_11_01.red",
    ])

    assert find_channels(node) == [
        "other.Mask_prop_01_01",
        "other.Mask_prop_01_03",
        "other.Mask_prop_02_01",
        "other.Mask_prop_10_01",
    ]


def test_find_channels_supports_multiple_glob_patterns():
    node = _Node([
        "other.kesha_mask",
        "other.foxy_mask",
        "other.Mask_prop_01_01",
        "other.depth",
    ])

    assert find_channels(
        node,
        pattern="Mask_prop_*,*_mask"
    ) == [
        "other.foxy_mask",
        "other.kesha_mask",
        "other.Mask_prop_01_01",
    ]
