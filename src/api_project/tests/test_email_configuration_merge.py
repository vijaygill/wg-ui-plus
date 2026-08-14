"""Additional CR-5 coverage: merged env/DB delivery path and status reporting.

These tests close the remaining coverage gaps around the effective
configuration merge:

* ``send_test_email()`` must use the merged effective configuration when ONLY a
  boolean environment variable (e.g. ``EMAIL_USE_TLS``) is present and every
  other value comes from the database row.
* ``get_email_status()`` reports ``configured`` for a fully configured database
  row with no environment variables and ``unavailable`` for a fresh row with no
  environment variables (verified both directly and through the endpoint).
"""

import io
from datetime import datetime, timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import management
from django.test import TestCase
from rest_framework.test import APIClient

from api_app.email_service import (
    EmailConfigurationError,
    _resolved_environment,
    get_email_status,
    send_test_email,
)
from api_app.models import ServerConfiguration


def make_configuration(**overrides):
    values = {
        "network_address": "192.168.2.0/24",
        "ip_address": "192.168.2.1",
        "host_name_external": "vpn.example.test",
        "port_external": 1196,
        "port_internal": 51820,
        "upstream_dns_ip_address": "192.168.0.5",
        "wireguard_config_path": "/config/wireguard/wg0.conf",
        "script_path_post_down": "/config/post-down.sh",
        "script_path_post_up": "/config/post-up.sh",
        "peer_default_port": 1196,
        "last_changed_datetime": datetime.now(timezone.utc),
    }
    values.update(overrides)
    return ServerConfiguration.objects.create(**values)


def save_email_fields(configuration, **overrides):
    values = {
        "email_host": "db-mail.local",
        "email_port": 2525,
        "email_host_user": "db-user@mail.local",
        "email_host_password": "db-secret",
        "email_default_from_email": "db-sender@mail.local",
        "email_use_tls": False,
        "email_use_ssl": False,
    }
    values.update(overrides)
    for field, value in values.items():
        setattr(configuration, field, value)
    configuration.save(update_fields=list(values.keys()))
    return values


class EmailStatusReportingTests(TestCase):
    def setUp(self):
        self.configuration = make_configuration()

    @patch.dict("os.environ", {}, clear=True)
    def test_status_configured_for_fully_configured_database_row(self):
        save_email_fields(self.configuration)
        status = get_email_status(configuration=self.configuration)
        self.assertEqual("configured", status["status"])

    @patch.dict("os.environ", {}, clear=True)
    def test_status_unavailable_for_fresh_database_row(self):
        status = get_email_status(configuration=self.configuration)
        self.assertEqual("unavailable", status["status"])

    @patch.dict("os.environ", {}, clear=True)
    def test_endpoint_reports_configured_for_fully_configured_database_row(self):
        save_email_fields(self.configuration)
        user = get_user_model().objects.create_user("admin", password="password")
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get("/api/v1/control/email/configuration")
        self.assertEqual(200, response.status_code)
        self.assertEqual("configured", response.json()["effective"]["status"])

    @patch.dict("os.environ", {}, clear=True)
    def test_endpoint_reports_unavailable_for_fresh_database_row(self):
        user = get_user_model().objects.create_user("admin", password="password")
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get("/api/v1/control/email/configuration")
        self.assertEqual(200, response.status_code)
        self.assertEqual("unavailable", response.json()["effective"]["status"])


class EmailBooleanOnlyEnvironmentMergeTests(TestCase):
    def setUp(self):
        self.configuration = make_configuration()

    @patch.dict("os.environ", {"EMAIL_USE_TLS": "True"}, clear=True)
    def test_merged_environment_keeps_database_values_but_toggles_tls(self):
        save_email_fields(self.configuration)
        merged = _resolved_environment(configuration=self.configuration)
        self.assertEqual("True", merged["EMAIL_USE_TLS"])
        self.assertEqual("db-mail.local", merged["EMAIL_HOST"])
        self.assertEqual("2525", merged["EMAIL_PORT"])
        self.assertEqual("db-user@mail.local", merged["EMAIL_HOST_USER"])
        self.assertEqual("db-secret", merged["EMAIL_HOST_PASSWORD"])
        self.assertEqual("db-sender@mail.local", merged["EMAIL_DEFAULT_FROM_EMAIL"])
        self.assertEqual("false", merged["EMAIL_USE_SSL"])

    @patch.dict("os.environ", {"EMAIL_USE_TLS": "True"}, clear=True)
    @patch("api_app.email_service.EmailBackend")
    @patch("api_app.email_service.EmailMessage")
    def test_send_test_email_uses_database_fields_with_boolean_env_override(
        self, email_class, backend_class
    ):
        save_email_fields(self.configuration)
        send_test_email()
        backend_class.assert_called_once_with(
            host="db-mail.local",
            port=2525,
            username="db-user@mail.local",
            password="db-secret",
            use_tls=True,
            use_ssl=False,
            fail_silently=False,
        )
        email_class.assert_called_once()
        self.assertIs(
            backend_class.return_value,
            email_class.call_args.kwargs["connection"],
        )
        email_class.return_value.send.assert_called_once_with(fail_silently=False)

    @patch.dict("os.environ", {"EMAIL_USE_SSL": "False"}, clear=True)
    @patch("api_app.email_service.EmailBackend")
    @patch("api_app.email_service.EmailMessage")
    def test_send_test_email_false_boolean_environment_does_not_override_database_security_mode(
        self, email_class, backend_class
    ):
        # EMAIL_USE_SSL="False" no longer counts as set, so the database TLS
        # value is honored and delivery proceeds with use_tls=True.
        save_email_fields(self.configuration, email_use_tls=True)
        send_test_email()
        backend_class.assert_called_once_with(
            host="db-mail.local",
            port=2525,
            username="db-user@mail.local",
            password="db-secret",
            use_tls=True,
            use_ssl=False,
            fail_silently=False,
        )

    @patch.dict("os.environ", {"EMAIL_USE_TLS": "False"}, clear=True)
    def test_false_boolean_environment_does_not_override_database_true(self):
        save_email_fields(self.configuration, email_use_tls=True)
        merged = _resolved_environment(configuration=self.configuration)
        self.assertEqual("true", merged["EMAIL_USE_TLS"])
        self.assertEqual("false", merged["EMAIL_USE_SSL"])

    @patch.dict("os.environ", {"EMAIL_USE_SSL": "true"}, clear=True)
    def test_conflicting_boolean_env_override_marks_effective_config_invalid(self):
        # Per-field merge: EMAIL_USE_SSL=true from the environment plus
        # email_use_tls=True from the database produces both security modes
        # enabled. The conflict is surfaced as an explicit invalid status (and
        # an EmailConfigurationError from send_test_email), never silently
        # resolved in favour of the environment value.
        save_email_fields(self.configuration, email_use_tls=True)

        with self.assertRaises(EmailConfigurationError) as raised:
            send_test_email()
        self.assertIn("cannot both be enabled", str(raised.exception))

    @patch.dict("os.environ", {"EMAIL_USE_TLS": "on"}, clear=True)
    def test_startup_seeding_does_not_destroy_database_values_when_only_boolean_set(self):
        # Regression guard: seeding with only EMAIL_USE_TLS present must not
        # clear the database host/port/from values.
        save_email_fields(self.configuration)
        management.call_command("db_init_db_on_start", stdout=io.StringIO())
        self.configuration.refresh_from_db()
        self.assertTrue(self.configuration.email_use_tls)
        self.assertEqual("db-mail.local", self.configuration.email_host)
        self.assertEqual(2525, self.configuration.email_port)
        self.assertEqual("db-sender@mail.local", self.configuration.email_default_from_email)
        self.assertEqual("db-secret", self.configuration.email_host_password)
