# -*- coding: utf-8 -*-

import os
import re


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(
        ROOT,
        *relative_path.split("/")
    )
    with open(path, "r") as handle:
        return handle.read()


def test_base_stylesheet_uses_shared_palette_and_geometry_tokens():
    stylesheet_source = _read(
        "scripts/script_toolbox/style/stylesheet.py"
    )
    palette_source = _read(
        "scripts/script_toolbox/style/palette.py"
    )
    metrics_source = _read(
        "scripts/script_toolbox/style/metrics.py"
    )

    assert "from . import palette" in stylesheet_source
    assert "from . import metrics" in stylesheet_source
    assert "_STYLE_VALUES = dict(vars(palette))" in stylesheet_source
    assert "_STYLE_VALUES.update(vars(metrics))" in stylesheet_source

    # Theme colors belong in palette.py. Keeping hex literals out of the base
    # stylesheet prevents a second source of truth from appearing over time.
    assert re.search(r"#[0-9a-fA-F]{6}", stylesheet_source) is None

    tokens = set(
        re.findall(r"%\(([A-Z][A-Z0-9_]*)\)s", stylesheet_source)
    )
    palette_names = set(
        re.findall(
            r"^([A-Z][A-Z0-9_]*)\s*=",
            palette_source,
            re.MULTILINE,
        )
    )
    metric_names = set(
        re.findall(
            r"^([A-Z][A-Z0-9_]*)\s*=",
            metrics_source,
            re.MULTILINE,
        )
    )

    assert tokens
    assert tokens.issubset(palette_names | metric_names)
    assert tokens & metric_names
