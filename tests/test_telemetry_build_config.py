# -*- coding: utf-8 -*-

from pathlib import Path

from tools import stamp_telemetry_config


ROOT = Path(__file__).resolve().parents[1]


def test_source_build_config_does_not_commit_project_token():
    path = (
        ROOT /
        "scripts" /
        "script_toolbox" /
        "telemetry" /
        "build_config.py"
    )
    text = path.read_text(encoding="utf-8")

    assert 'POSTHOG_PROJECT_TOKEN = ""' in text
    assert 'POSTHOG_HOST = "https://eu.i.posthog.com"' in text


def test_stamper_embeds_build_token_without_changing_provider_contract(tmp_path):
    path = tmp_path / "build_config.py"

    assert stamp_telemetry_config.stamp(
        path,
        "phc_test",
        "https://eu.i.posthog.com",
    ) is True

    text = path.read_text(encoding="utf-8")
    assert 'POSTHOG_PROJECT_TOKEN = "phc_test"' in text
    assert 'POSTHOG_HOST = "https://eu.i.posthog.com"' in text


def test_official_build_workflows_use_posthog_secret():
    dev_workflow = (
        ROOT / ".github" / "workflows" / "dev-build.yml"
    ).read_text(encoding="utf-8")
    release_workflow = (
        ROOT / ".github" / "workflows" / "release.yml"
    ).read_text(encoding="utf-8")

    for workflow in (dev_workflow, release_workflow):
        assert "secrets.POSTHOG_PROJECT_TOKEN" in workflow
        assert "python tools/stamp_telemetry_config.py" in workflow
