# -*- coding: utf-8 -*-
"""Stamp public analytics client configuration into an official package build."""

from __future__ import print_function

import argparse
import json
import os
from pathlib import Path


DEFAULT_PATH = Path(
    "scripts/script_toolbox/telemetry/build_config.py"
)
DEFAULT_POSTHOG_HOST = "https://eu.i.posthog.com"


def render_config(project_token, host):
    token_literal = json.dumps(project_token or "")
    host_literal = json.dumps(host or DEFAULT_POSTHOG_HOST)
    return (
        '# -*- coding: utf-8 -*-\n'
        '"""Build-time telemetry configuration.\n\n'
        'This file is stamped in official packages by GitHub Actions.\n'
        'The PostHog project token is a public, write-only ingestion token.\n'
        '"""\n\n'
        'POSTHOG_HOST = {0}\n'
        'POSTHOG_PROJECT_TOKEN = {1}\n\n\n'
        '__all__ = [\n'
        '    "POSTHOG_HOST",\n'
        '    "POSTHOG_PROJECT_TOKEN",\n'
        ']\n'
    ).format(host_literal, token_literal)


def stamp(path, project_token, host):
    path = Path(path)
    path.write_text(
        render_config(project_token, host),
        encoding="utf-8"
    )
    return bool(project_token)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        default=str(DEFAULT_PATH)
    )
    args = parser.parse_args(argv)

    project_token = os.environ.get(
        "POSTHOG_PROJECT_TOKEN",
        ""
    ).strip()
    host = os.environ.get(
        "POSTHOG_HOST",
        DEFAULT_POSTHOG_HOST
    ).strip() or DEFAULT_POSTHOG_HOST

    configured = stamp(
        args.path,
        project_token,
        host
    )

    # Never print or otherwise expose the project token in CI logs.
    print(
        "Telemetry build config: {0}; host={1}".format(
            "configured" if configured else "disabled",
            host
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
