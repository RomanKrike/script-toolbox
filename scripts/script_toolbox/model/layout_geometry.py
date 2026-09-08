# -*- coding: utf-8 -*-
from __future__ import print_function


def distribution_spacer_positions(
    distribution,
    count,
    start_value,
    end_value
):
    """Return QBoxLayout spacer slots for a one-dimensional distribution.

    Slots are numbered from 0 (before the first child) through ``count``
    (after the last child). The function is Qt-free so layout semantics are
    directly unit-testable.
    """
    count = max(
        0,
        int(count)
    )
    if count <= 0:
        return ()

    if distribution == end_value:
        return (0,)

    if distribution == "center":
        return (
            0,
            count,
        )

    if distribution == "space_between":
        if count == 1:
            return (count,)
        return tuple(
            range(
                1,
                count
            )
        )

    # Start alignment (left/top) is the default.
    return (count,)


__all__ = [
    "distribution_spacer_positions",
]
