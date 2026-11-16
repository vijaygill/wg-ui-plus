"""Tests for the environment-driven DEBUG setting (REV-07).

The settings module is imported in a subprocess with a controlled
environment: Django's test runner forces DEBUG=False in-process, so an
in-process assertion would be vacuous, and reloading api_project.settings
mid-suite would re-run its FastMCP, logging and database configuration.
"""

import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

# Directory that contains the api_project settings package, i.e. the Django
# project directory (parent of the api_app package).
PROJECT_DIR = str(Path(sys.modules["api_app"].__file__).resolve().parent.parent)


def _run_settings_import(extra_env=None):
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "api_project.settings"}
    env.pop("DJANGO_DEBUG", None)
    # A sentinel key makes the SECRET_KEY expression short-circuit here, so
    # importing settings in this subprocess never reads or creates the real
    # /data/secret_key file. These tests assert only on DEBUG.
    env["DJANGO_SECRET_KEY"] = "test-sentinel-value-not-a-real-key"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "from django.conf import settings; print(settings.DEBUG)",
        ],
        cwd=PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


class SettingsDebugEnvironmentTests(SimpleTestCase):
    def test_debug_disabled_when_environment_unset(self):
        completed = _run_settings_import()
        self.assertEqual(
            completed.returncode,
            0,
            f"settings import failed: stdout={completed.stdout!r} "
            f"stderr={completed.stderr!r}",
        )
        self.assertTrue(
            completed.stdout.strip().endswith("False"),
            f"expected DEBUG to default to False, got stdout="
            f"{completed.stdout!r} stderr={completed.stderr!r}",
        )

    def test_debug_enabled_when_environment_set(self):
        completed = _run_settings_import({"DJANGO_DEBUG": "true"})
        self.assertEqual(
            completed.returncode,
            0,
            f"settings import failed: stdout={completed.stdout!r} "
            f"stderr={completed.stderr!r}",
        )
        self.assertTrue(
            completed.stdout.strip().endswith("True"),
            f"expected DJANGO_DEBUG=true to enable DEBUG, got stdout="
            f"{completed.stdout!r} stderr={completed.stderr!r}",
        )
