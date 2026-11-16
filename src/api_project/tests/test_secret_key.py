"""Tests for the environment-or-generated SECRET_KEY handling (REV-08).

The file logic is exercised by calling the settings helper with paths inside a
temporary directory. No test asserts on or modifies the real
``/data/secret_key``; the file logic runs only against temporary-directory
paths. Importing settings -- which pytest-django does before collection --
still creates ``/data/secret_key`` on a machine that has none unless
``DJANGO_SECRET_KEY`` is set; the subprocess tests set a sentinel key so they
never take that path. The environment-variable case is asserted in a child
process because the runner has already evaluated Django's in-process settings
by the time tests run, which would make an in-process assertion vacuous.
"""

import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

# Directory that contains the api_project settings package, i.e. the Django
# project directory (parent of the api_app package).
PROJECT_DIR = str(Path(sys.modules["api_app"].__file__).resolve().parent.parent)

# The runner has already imported the settings module, so this reuses that
# module object instead of re-running its configuration.
_load_secret_key = sys.modules["api_project.settings"]._load_secret_key


class SecretKeyEnvironmentTests(SimpleTestCase):
    def test_secret_key_taken_from_environment(self):
        env = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "api_project.settings",
            "DJANGO_SECRET_KEY": "sentinel-value",
        }
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "from django.conf import settings; print(settings.SECRET_KEY)",
            ],
            cwd=PROJECT_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"settings import failed: stdout={completed.stdout!r} "
            f"stderr={completed.stderr!r}",
        )
        self.assertEqual(
            completed.stdout.strip(),
            "sentinel-value",
            f"expected DJANGO_SECRET_KEY to be used as SECRET_KEY, got stdout="
            f"{completed.stdout!r} stderr={completed.stderr!r}",
        )


class LoadSecretKeyFileTests(SimpleTestCase):
    def test_creates_key_file_with_private_mode(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "secret_key")
            key = _load_secret_key(key_file)
            self.assertTrue(key, "expected a non-empty generated key")
            self.assertTrue(
                os.path.exists(key_file),
                "expected the key to be persisted for the next start",
            )
            self.assertEqual(
                stat.S_IMODE(os.stat(key_file).st_mode),
                0o600,
                "expected the key file to be readable only by its owner",
            )

    def test_second_call_returns_the_persisted_key(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "secret_key")
            first = _load_secret_key(key_file)
            second = _load_secret_key(key_file)
            self.assertEqual(
                second,
                first,
                "expected the stored key to survive a restart",
            )
            with open(key_file) as handle:
                self.assertEqual(handle.read(), first)

    def test_existing_file_content_is_used_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "secret_key")
            with open(key_file, "w") as handle:
                handle.write("pre-existing-key")
            self.assertEqual(_load_secret_key(key_file), "pre-existing-key")
            with open(key_file) as handle:
                self.assertEqual(
                    handle.read(),
                    "pre-existing-key",
                    "expected an existing key file to be left untouched",
                )

    def test_unusable_path_returns_ephemeral_key_without_raising(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "missing-dir", "secret_key")
            key = _load_secret_key(key_file)
            self.assertTrue(
                key,
                "expected a temporary key instead of an exception when the "
                "key file cannot be read or written",
            )
            self.assertFalse(os.path.exists(key_file))

    def test_surrounding_whitespace_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "secret_key")
            with open(key_file, "w") as handle:
                handle.write("key\n")
            self.assertEqual(_load_secret_key(key_file), "key")

    def test_empty_file_is_repaired_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "secret_key")
            open(key_file, "w").close()
            key = _load_secret_key(key_file)
            self.assertTrue(
                key,
                "expected an empty key file to be repaired instead of "
                "accepted as the secret key",
            )
            with open(key_file) as handle:
                self.assertEqual(
                    handle.read(),
                    key,
                    "expected the repaired key to be persisted for the next "
                    "start",
                )

    def test_whitespace_only_file_is_repaired_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "secret_key")
            with open(key_file, "w") as handle:
                handle.write("\n  \n")
            key = _load_secret_key(key_file)
            self.assertTrue(
                key,
                "expected a whitespace-only key file to be repaired instead "
                "of accepted as the secret key",
            )
            with open(key_file) as handle:
                self.assertEqual(handle.read(), key)

    def test_private_mode_preserved_on_repair(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "secret_key")
            with open(key_file, "w") as handle:
                handle.write("")
            os.chmod(key_file, 0o600)
            _load_secret_key(key_file)
            self.assertEqual(
                stat.S_IMODE(os.stat(key_file).st_mode),
                0o600,
                "expected a repaired key file to stay readable only by its "
                "owner",
            )

    def test_no_temporary_file_left_on_success(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "secret_key")
            _load_secret_key(key_file)
            self.assertEqual(
                os.listdir(tmp_dir),
                ["secret_key"],
                "expected the atomic write to leave no temporary file "
                "behind",
            )

    def test_unwritable_path_leaves_no_litter_and_never_raises(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "missing-dir", "secret_key")
            try:
                key = _load_secret_key(key_file)
            except OSError as exc:
                self.fail(f"expected no exception, got {exc!r}")
            self.assertTrue(
                key,
                "expected a temporary key when the key file cannot be "
                "written",
            )
            self.assertFalse(os.path.exists(key_file))
            self.assertEqual(os.listdir(tmp_dir), [])

    def test_undecodable_file_is_repaired_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "secret_key")
            with open(key_file, "wb") as handle:
                handle.write(b"\xff\xfe\x00broken")
            try:
                key = _load_secret_key(key_file)
            except Exception as exc:
                self.fail(f"expected no exception, got {exc!r}")
            self.assertTrue(
                key,
                "expected an undecodable key file to be repaired with a "
                "generated key instead of raising",
            )
            with open(key_file) as handle:
                self.assertEqual(
                    handle.read(),
                    key,
                    "expected the repaired key to be persisted for the next "
                    "start",
                )
            self.assertEqual(
                stat.S_IMODE(os.stat(key_file).st_mode),
                0o600,
                "expected the repaired key file to be readable only by its "
                "owner",
            )

    def test_foreign_temp_file_survives_repair(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, "secret_key")
            decoy = f"{key_file}.{os.getpid()}.tmp"
            with open(decoy, "w") as handle:
                handle.write("someone-else-s-data")
            key = _load_secret_key(key_file)
            self.assertTrue(
                os.path.exists(decoy),
                "expected a pre-existing temp-named file to be left alone",
            )
            with open(decoy) as handle:
                self.assertEqual(
                    handle.read(),
                    "someone-else-s-data",
                    "expected the foreign temp file to keep its content",
                )
            self.assertTrue(
                os.path.exists(key_file),
                "expected the key file to be created despite the decoy",
            )
            self.assertTrue(key)
            with open(key_file) as handle:
                self.assertEqual(handle.read(), key)

    def test_symlink_is_preserved_and_repaired_through(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = os.path.join(tmp_dir, "mounted-secret")
            key_file = os.path.join(tmp_dir, "secret_key")
            open(target, "w").close()
            os.symlink(target, key_file)
            key = _load_secret_key(key_file)
            self.assertTrue(key)
            self.assertTrue(
                os.path.islink(key_file),
                "expected the repair to keep the symlink in place",
            )
            with open(target) as handle:
                self.assertEqual(
                    handle.read(),
                    key,
                    "expected the repaired key to be written through the "
                    "symlink to its target",
                )
            self.assertEqual(
                stat.S_IMODE(os.stat(key_file).st_mode),
                0o600,
                "expected the repaired key to stay readable only by its "
                "owner",
            )
