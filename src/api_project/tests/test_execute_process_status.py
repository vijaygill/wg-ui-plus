import subprocess
import types
from unittest import mock

from django.test import SimpleTestCase

from api_app.wireguard_helper import WireGuardHelper


def make_server_configuration(**overrides):
    """Build a lightweight fake ServerConfiguration the helper can read."""
    defaults = {
        "wireguard_config_path": "/config/wireguard/wg0.conf",
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


class ExecuteProcessStatusTests(SimpleTestCase):
    def test_successful_command_returns_zero_returncode(self):
        helper = WireGuardHelper()
        returncode, output = helper.execute_process('sh -c "echo hello; exit 0"')
        self.assertEqual(returncode, 0)
        self.assertIn("hello", output)

    def test_failing_command_returns_nonzero_returncode(self):
        helper = WireGuardHelper()
        returncode, output = helper.execute_process("/bin/false")
        self.assertNotEqual(returncode, 0)
        self.assertIsInstance(output, str)

    def test_timeout_kills_drains_and_reports_failure(self):
        helper = WireGuardHelper()
        fake_proc = mock.Mock()
        fake_proc.communicate.side_effect = [
            subprocess.TimeoutExpired("cmd", 60),
            (b"partial ", b""),
        ]
        with mock.patch(
            "api_app.wireguard_helper.subprocess.Popen", return_value=fake_proc
        ):
            returncode, output = helper.execute_process("sleep 999")
        fake_proc.kill.assert_called_once()
        # Second communicate() call drains the pipes after the kill.
        self.assertEqual(fake_proc.communicate.call_count, 2)
        fake_proc.communicate.assert_called_with()
        self.assertNotEqual(returncode, 0)
        self.assertIn("command timed out", output)
        self.assertIn("partial", output)


class RestartStatusTests(SimpleTestCase):
    def test_restart_reports_error_on_nonzero_returncode(self):
        helper = WireGuardHelper()
        sc = make_server_configuration()
        with mock.patch.object(
            helper, "execute_process", return_value=(1, "wg-quick failed")
        ):
            res = helper.restart(sc)
        self.assertNotEqual(res["status"], "ok")
        self.assertIn("wg-quick failed", res["output"])

    def test_restart_reports_ok_on_zero_returncode(self):
        helper = WireGuardHelper()
        sc = make_server_configuration()
        with mock.patch.object(
            helper, "execute_process", return_value=(0, "done")
        ):
            res = helper.restart(sc)
        self.assertEqual(res["status"], "ok")
        self.assertIn("done", res["output"])
