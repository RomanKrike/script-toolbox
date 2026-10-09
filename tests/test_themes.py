"""Portable themes validate before altering settings and retain other preferences."""
import json

import pytest

from script_toolbox.core import themes
from script_toolbox.core.preferences import load_preferences, save_preferences


@pytest.mark.parametrize("change", [
    {"version": 3}, {"version": True}, {"name": " "}, {"name": "x" * 81},
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


def test_upgrade_eight_color_theme():
    colors = dict((key, color) for key, label, color in themes.ROLES[:8])
    colors["input"] = "#123456"
    old = {"version": 1, "name": "Studio", "colors": colors}
    upgraded = themes.validate(old)
    assert upgraded["version"] == themes.VERSION
    assert upgraded["colors"]["input"] == "#123456"
    assert upgraded["colors"]["expression_error"] == themes.DEFAULT_COLORS["expression_error"]
    assert old["colors"] == colors and len(colors) == 8
