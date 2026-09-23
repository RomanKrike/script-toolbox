# -*- coding: utf-8 -*-
from __future__ import print_function

from .preferences import load_preferences
from .preferences import save_preferences


WINDOW_GEOMETRY_KEY = "window_geometry"
MIN_WINDOW_WIDTH = 160
MIN_WINDOW_HEIGHT = 120
MAX_WINDOW_EXTENT = 100000


def normalize_window_geometry(value):
    """Return a safe persisted geometry dictionary or ``None``."""
    if not isinstance(value, dict):
        return None

    result = {}
    for key in (
        "x",
        "y",
        "width",
        "height",
    ):
        try:
            result[key] = int(
                value[key]
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            return None

    if result["width"] < MIN_WINDOW_WIDTH:
        return None
    if result["height"] < MIN_WINDOW_HEIGHT:
        return None
    if result["width"] > MAX_WINDOW_EXTENT:
        return None
    if result["height"] > MAX_WINDOW_EXTENT:
        return None

    return result


def get_window_geometry(path=None):
    preferences = load_preferences(
        path=path
    )
    return normalize_window_geometry(
        preferences.get(
            WINDOW_GEOMETRY_KEY
        )
    )


def set_window_geometry(
    geometry,
    path=None
):
    geometry = normalize_window_geometry(
        geometry
    )

    if geometry is None:
        return None

    preferences = load_preferences(
        path=path
    )
    preferences[
        WINDOW_GEOMETRY_KEY
    ] = geometry
    save_preferences(
        preferences,
        path=path
    )
    return geometry


__all__ = [
    "MAX_WINDOW_EXTENT",
    "MIN_WINDOW_HEIGHT",
    "MIN_WINDOW_WIDTH",
    "WINDOW_GEOMETRY_KEY",
    "get_window_geometry",
    "normalize_window_geometry",
    "set_window_geometry",
]
