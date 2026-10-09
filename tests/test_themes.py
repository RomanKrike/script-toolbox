"""Portable themes validate before altering settings and retain other preferences."""
import json

import pytest

from script_toolbox.core import themes
from script_toolbox.core.preferences import load_preferences, save_preferences
from script_toolbox.style.themes import color_map


def test_default_palette_and_tonal_offsets():
    from script_toolbox.style import palette
    mapping = color_map(themes.DEFAULT_COLORS)
    assert all(source == target for source, target in mapping.items())
    changed = dict(themes.DEFAULT_COLORS, input="#202020")
    mapping = color_map(changed)
    assert mapping[palette.INPUT_BG] == "#202020"
    assert mapping[palette.WINDOW_BG] == palette.WINDOW_BG
    assert themes.builtins()[0] == themes.theme()


@pytest.mark.parametrize("change", [
    {"version": 2}, {"version": True}, {"name": " "}, {"name": "x" * 81},
    {"colors": {}}, {"colors": dict(themes.DEFAULT_COLORS, text="red")},
    {"colors": dict(themes.DEFAULT_COLORS, layout="#ffffff")},
])
def test_reject_invalid_theme(change):
    value = themes.theme()
    value.update(change)
    with pytest.raises(ValueError):
        themes.validate(value)


def test_theme_round_trip_and_preference_isolation(tmp_path, monkeypatch):
    settings = str(tmp_path / "settings.json")
    monkeypatch.setattr(themes, "load_preferences", lambda: load_preferences(settings))
    monkeypatch.setattr(themes, "save_preferences", lambda prefs: save_preferences(prefs, settings))
    save_preferences({"other_setting": {"keep": True}}, settings)
    value = themes.theme("My theme", dict(themes.DEFAULT_COLORS, input="#202020"))
    path = str(tmp_path / "theme.json")
    themes.write_theme(path, value)
    assert themes.read_theme(path) == value
    assert set(json.loads((tmp_path / "theme.json").read_text())) == {"version", "name", "colors"}
    themes.save_state(value, [value])
    assert themes.load_state() == (value, [value])
    assert load_preferences(settings)["other_setting"] == {"keep": True}
    assert themes.theme()["colors"]["input"] == "#27292c"
